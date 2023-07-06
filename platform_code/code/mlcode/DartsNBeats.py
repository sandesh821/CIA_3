#Copyright (c) Microsoft. All rights reserved.
from DARTS import DARTS
from darts.models import NBEATSModel
import logging
import pandas as pd
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


class DartsNBeats(DARTS):
    def __init__(self,params):
        super().__init__(params)
        self.__preprocessData__()
        self.modelType = self.modelName
        self.outputPath = self.modelPath

    def trainModel(self):
        logging.info("Start: Model Training")
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
            self.nbeats_model = NBEATSModel(
                input_chunk_length=self.lookback,
                output_chunk_length=self.horizon,
                generic_architecture=True,
                num_stacks=self.parameters["num_stacks"],
                num_blocks=self.parameters["num_blocks"],
                num_layers=self.parameters["num_layers"],
                layer_widths=self.parameters["layer_widths"],
                n_epochs=self.parameters["n_epochs"],
                nr_epochs_val_period=self.parameters["nr_epochs_val_period"],
                batch_size=self.parameters["batch_size"],
                model_name='nbeats_run',
                pl_trainer_kwargs={
                    "enable_progress_bar": self.parameters["verbose"],
                    "callbacks": database_update_callbacks
                }
            )   
        except Exception as ex:
            logging.error("Error in model initialization.")
            logging.error(ex)
            raise ex
                             
        try:
            self.nbeats_model.fit(self.train,
                            past_covariates=self.train_cov,
                            val_series=self.validat,
                            val_past_covariates=self.val_cov,
                            verbose=self.parameters["verbose"]
                            # num_loader_workers = 2
                            )
            self.trainer = self.nbeats_model.trainer
            logging.info("End: Model Training")
        except Exception as ex:
            logging.error("Error in fitting model.")
            logging.error(ex)
            raise ex
        if 'objective' not in inspect.stack()[1]:
            update_training_status(AMLRunId,TRAINING_END,None,-1,None,None,ChildAMLRunId,None)
        return self.__saveModel__([self.trainer,self.nbeats_model],self.modelType)

    def testModel(self):
        try:
            # Compute the backtest predictions with the two models
            self.predSeries = self.nbeats_model.historical_forecasts(self.dataPreprocessedData,
                                                        past_covariates=self.dataPreprocessedCovariatesData,
                                                        start=pd.Timestamp(self.train_end),
                                                        forecast_horizon=self.forecast_params["forecast_horizon"],
                                                        retrain=False,
                                                        verbose=self.forecast_params["verbose"])
        except Exception as ex:
            logging.error("Error in model validation.")
            logging.error(ex)
            raise ex
        rmsescore = self.__rmse__()
        self.__saveValData__(self.valData,self.modelType)
        return rmsescore

    def objective(trial,datasetPath,trainParams,n_trials):
        params ={
            "datasetPath":datasetPath,
            "modelPath":trainParams["modelPath"],
            "dataFileName":trainParams["dataFileName"],
            "modelName":"DartsNBeats",
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
            "parameters" : {"num_stacks":trial.suggest_int('num_stacks',5,30,step=5),
                            "num_blocks":trial.suggest_int('num_blocks',1,5),
                            "num_layers":trial.suggest_int('num_layers', 1,5),
                            "layer_widths":trial.suggest_int('layer_widths', 256,1024,step=256),
                            "n_epochs": trial.suggest_int('n_epochs', 1, 4,step=1),
                            "batch_size":trial.suggest_int('batch_size', 32 ,64, step=32),
                            "nr_epochs_val_period":1,
                            "verbose":True},
            "forecast_params": {"n":6,
                                "forecast_horizon":trainParams["forecast_params"]["forecast_horizon"],
                                "verbose":False}
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

        model = DartsNBeats(params)

        status = TRAINING_HYPER_PARAMETER_TUNING
        update_training_status(AMLRunId,status,total_epoch,-1,n_trials,trial.number,ChildAMLRunId,None)
        modelFilePath = model.trainModel()

        status = TESTING_HYPER_PARAMETER_TUNING
        update_training_status(AMLRunId,status,total_epoch,-1,n_trials,trial.number,ChildAMLRunId,None)
        rmse = model.testModel()

        status = FINISHING_HYPER_PARAMETER_TUNING
        update_training_status(AMLRunId,status,total_epoch,-1,n_trials,trial.number,ChildAMLRunId,None)

        return rmse