#Copyright (c) Microsoft. All rights reserved.
import warnings
warnings.filterwarnings("ignore")

from DARTS import DARTS
from darts.models import TCNModel
import logging
import pandas as pd
import optuna 
import numba
import inspect

from torchCallbacks import TorchTrainingLossDatabaseUpdateCallback
from dboperations.dboperations import executeStoredProcedure
from logUtils import get_AMLRunId, update_training_status, get_ChildAMLRunId
from logConfig import (
    TRAINING_START,
    TRAINING_END,
    RUNNING_HYPER_PARAMETER_TUNING, 
    TRAINING_HYPER_PARAMETER_TUNING, 
    TESTING_HYPER_PARAMETER_TUNING,
    FINISHING_HYPER_PARAMETER_TUNING
)


class DartsTCN(DARTS):
    def __init__(self,params):
        super().__init__(params)
        self.__preprocessData__()
        self.modelType = self.modelName
        self.valData = None
        self.outputPath = self.modelPath
    
    def trainModel(self):
        logging.info("=========Start: Model Training=========")
        logging.info("=========Start: Model Training=========")
        
        self.__buildTrainTestDataSet__()
        
        AMLRunId = get_AMLRunId(modelPath=self.outputPath)
        ChildAMLRunId = get_ChildAMLRunId(modelPath=self.outputPath)
        print("inspect.stack()[1][3]", inspect.stack()[1][3])
        if 'objective' not in inspect.stack()[1]:
            update_training_status(AMLRunId,TRAINING_START,None,-1,None,None,ChildAMLRunId,None)
        
        try:
            params = self.modelType, self.modelPath
            # Check if the objective function is being called (i.e. if hyperparameter tuning is happening) if 'objective' is not inspect.stack()[1][3] 
            # If not, add the database update callback callbacks.append(TorchTrainingLossDatabaseUpdateCallback(params)) 
            database_update_callbacks = []
            if 'objective' not in inspect.stack()[1]:
                # If not, add the database update callback
                database_update_callbacks.append(TorchTrainingLossDatabaseUpdateCallback(params))        
            self.tcn_model_cov = TCNModel(
                input_chunk_length=self.lookback, #this corresponds to the lookback window of the model
                output_chunk_length=self.horizon, #this is the horizon we’re interested to forecast
                n_epochs=self.parameters["n_epochs"],
                dropout=self.parameters["dropout"],
                dilation_base=self.parameters["dilation_base"],
                weight_norm=self.parameters["weight_norm"],
                kernel_size=self.parameters["kernel_size"],
                num_filters=self.parameters["num_filters"],
                random_state=self.parameters["random_state"],
                pl_trainer_kwargs={"callbacks": database_update_callbacks}
            )
        except Exception as ex:
            logging.error("Error in model initialization.")
            logging.error(ex)
            raise ex
        
        try:
            self.tcn_model_cov.fit(
                            series=self.train,
                            past_covariates=self.train_cov,
                            # val_series=self.validat,
                            # val_past_covariates=self.val_cov,
                            # num_loader_workers = 2,
                            verbose=self.parameters["verbose"],
            )
            self.trainer = self.tcn_model_cov.trainer
            self.model = self.tcn_model_cov
            #Save Trainer to be used for prediction
            logging.info("=========End: Model Training=========")
        except Exception as ex:
            logging.error("Error in fitting model.")
            logging.error(ex)
            raise ex
        
        print("Model training complete")
        if 'objective' not in inspect.stack()[1]:
            update_training_status(AMLRunId,TRAINING_END,None,-1,None,None,ChildAMLRunId,None)

        return self.__saveModel__([self.trainer,self.tcn_model_cov],self.modelType)

    def testModel(self):
        try:
            logging.info("=========Start: Model Evaluation=========")
            # Compute the backtest predictions with the two models
            self.predSeries = self.tcn_model_cov.historical_forecasts(
                                                                    self.dataPreprocessedData,
                                                                    past_covariates=self.dataPreprocessedCovariatesData,
                                                                    start=pd.Timestamp(self.train_end), 
                                                                    forecast_horizon=self.forecast_params["forecast_horizon"],
                                                                    retrain=False,
                                                                    last_points_only=True,
                                                                    verbose=self.forecast_params["verbose"]
                                                                    )
            logging.info("=========End: Model Evaluation=========")
        except Exception as ex:
            logging.error("Error in model validation.")
            logging.error(ex)
            raise ex
            
        rmsescore = self.__rmse__()

        self.__saveValData__(self.valData,self.modelType)
        return rmsescore

    def objective(trial,datasetPath,trainParams,n_trials):
        # print(trainParams["hyperparametersranges"]["DartsTCN"])
        # hyperparameterranges = trainParams["hyperparametersranges"]["DartsTCN"]
        # print(hyperparameterranges["dilation_base"][0], hyperparameterranges["dilation_base"][1][0],hyperparameterranges["dilation_base"][1][1],hyperparameterranges["dilation_base"][1][2])
        params ={
            "datasetPath":datasetPath,
            "dataFileName":trainParams["dataFileName"],
            "modelPath":trainParams["modelPath"],
            "modelName":"DartsTCN",
            "freq":trainParams["freq"],
            "frequency": trainParams["frequency"],
            "frequency_duration": trainParams["frequency_duration"],
            "multiplicationFactor": trainParams["multiplicationFactor"],
            "requiredColumns": trainParams['requiredColumns'],
            "targetColumn": trainParams["targetColumn"],
            "futureCovariates": trainParams["futureCovariates"],
            "dateField": trainParams["dateField"],
            "train_end": trainParams["train_end"],
            "val_end": trainParams["val_end"],
            "val_start": trainParams["val_start"],
            #Slicing hyperparameters
            "horizon":trainParams["horizon"],
            "lookback":trainParams["lookback"],
            "isOptimizationEnabled" : False,
            #architecture and training hyperparameters
            "parameters" : {"n_epochs": trial.suggest_int('n_epochs', 10, 80,step=10), 
                            "dropout":trial.suggest_float('dropout', 0.1, 0.5,step=0.1),
                            "dilation_base":trial.suggest_int('dilation_base', 1, 3),
                            "weight_norm":True,
                            "kernel_size":trial.suggest_categorical('kernel_size', [3, 7]),
                            "num_filters":trial.suggest_int('num_filters', 1, 4),
                            "random_state":0, 
                            "verbose":False},
            "forecast_params": {"n":6,
                                "forecast_horizon":trainParams["forecast_params"]["forecast_horizon"],
                                "verbose":False,
                                "last_points_only":True}
        }

        # retrieves the file path of the model being trained
        modelPath = params['modelPath']
        # retrieves the AML run ID associated with the model
        AMLRunId = get_AMLRunId(modelPath=modelPath)
        ChildAMLRunId = get_ChildAMLRunId(modelPath=modelPath)
        # calculate the total epoch completed
        total_epoch = params['parameters']['n_epochs']

        

        # update the status of the trial, first to "running", then to "training", then to "testing", and finally to "finished".
        
        status = RUNNING_HYPER_PARAMETER_TUNING
        update_training_status(AMLRunId,status,total_epoch,-1,n_trials,trial.number,ChildAMLRunId,None)

        model = DartsTCN(params)

        status = TRAINING_HYPER_PARAMETER_TUNING
        update_training_status(AMLRunId,status,total_epoch,-1,n_trials,trial.number,ChildAMLRunId,None)
        modelFilePath = model.trainModel()
        
        status = TESTING_HYPER_PARAMETER_TUNING
        update_training_status(AMLRunId,status,total_epoch,-1,n_trials,trial.number,ChildAMLRunId,None)
        rmse = model.testModel()

        status = FINISHING_HYPER_PARAMETER_TUNING
        update_training_status(AMLRunId,status,total_epoch,-1,n_trials,trial.number,ChildAMLRunId,None)
        
        return rmse