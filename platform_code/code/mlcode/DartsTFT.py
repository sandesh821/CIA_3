#Copyright (c) Microsoft. All rights reserved.
import warnings
warnings.filterwarnings("ignore")

import time
from DARTS import DARTS
from darts.models import TFTModel
import logging
import pandas as pd
import optuna
from pytorch_lightning.callbacks import EarlyStopping, LearningRateMonitor
from pytorch_forecasting.metrics import QuantileLoss
from pytorch_lightning.loggers import TensorBoardLogger
import pytorch_lightning as pl
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


class DartsTFT(DARTS):
    def __init__(self,params):
        super().__init__(params)
        self.__preprocessData__()
        self.modelType = self.modelName
        self.outputPath = self.modelPath
    
    def trainModel(self):
        logging.info("=========Start: Model Training=========")
        self.__buildTrainTestDataSet__()
        
        AMLRunId = get_AMLRunId(modelPath=self.outputPath)
        ChildAMLRunId = get_ChildAMLRunId(modelPath=self.outputPath)
        print("inspect.stack()[1][3]", inspect.stack()[1][3])
        if 'objective' not in inspect.stack()[1]:
            update_training_status(AMLRunId,TRAINING_START,None,-1,None,None,ChildAMLRunId,None)

        params = self.modelType, self.modelPath
        # Check if the objective function is being called (i.e. if hyperparameter tuning is happening) if 'objective' is not inspect.stack()[1][3] 
        # If not, add the database update callback callbacks.append(TorchTrainingLossDatabaseUpdateCallback(params)) 
        database_update_callbacks = []
        if 'objective' not in inspect.stack()[1]:
            # If not, add the database update callback
            database_update_callbacks.append(TorchTrainingLossDatabaseUpdateCallback(params))    
        pl_trainer_kwargs={"gradient_clip_val": 0.9939014314200116, "accelerator": "gpu", "gpus": 1, "callbacks": database_update_callbacks}

        optimizer_kwargs  = {'lr': self.parameters["lr"]}
        
        try:
            self.tft_model_cov = TFTModel(
                input_chunk_length=self.lookback,
                output_chunk_length=self.horizon,
                hidden_size = self.parameters["hidden_size"],
                hidden_continuous_size = self.parameters["hidden_continuous_size"],
                lstm_layers = self.parameters["lstm_layers"],
                num_attention_heads = self.parameters["num_attention_heads"],
                n_epochs=self.parameters["n_epochs"],
                dropout=self.parameters["dropout"],
                batch_size = self.parameters["batch_size"],
                add_relative_index=self.parameters["add_relative_index"],
                random_state=self.parameters["random_state"],
                optimizer_kwargs=optimizer_kwargs,
                pl_trainer_kwargs = pl_trainer_kwargs
                # loss_fn = QuantileLoss()
            )
        except Exception as ex:
            logging.error("Error in model initialization.")
            logging.error(ex)
            raise ex
        
        try:
            self.tft_model_cov.fit(
                        series=self.train,
                        past_covariates=self.train_cov,
                        future_covariates=self.train_fut_cov,
                        val_series=self.validat,
                        val_past_covariates=self.val_cov,
                        val_future_covariates = self.val_fut_cov,
                        num_loader_workers = 4,
                        verbose=self.parameters["verbose"])
            self.trainer = self.tft_model_cov.trainer
            #Save Trainer to be used for prediction
            logging.info("=========End: Model Training=========")
        except Exception as ex:
            logging.error("Error in fitting model.")
            logging.error(ex)
            raise ex
        if 'objective' not in inspect.stack()[1]:
            update_training_status(AMLRunId,TRAINING_END,None,-1,None,None,ChildAMLRunId,None)

        return self.__saveModel__([self.trainer,self.tft_model_cov],self.modelType)

    def testModel(self):
        try:
            self.dataPreprocessedFutureCovariates = self.dataPreprocessedFutureCovariates.shift(12)
            
            # Compute the backtest predictions with the two models
            self.predSeries = self.tft_model_cov.historical_forecasts(self.dataPreprocessedData,
                                                                    past_covariates=self.dataPreprocessedCovariatesData,
                                                                    future_covariates=self.dataPreprocessedFutureCovariates,
                                                                    start=pd.Timestamp(self.train_end),
                                                                    forecast_horizon=self.forecast_params["forecast_horizon"],
                                                                    retrain=False,
                                                                    last_points_only=True,
                                                                    verbose=self.forecast_params["verbose"])
        except Exception as ex:
            logging.error("Error in model validation.")
            logging.error(ex)
            raise ex
        rmsescore = self.__rmse__()
        self.__saveValData__(self.valData,self.modelType)
        return rmsescore

    def objective(trial,datasetPath, trainParams,n_trials):
        params ={
            "datasetPath":datasetPath,
            "dataFileName":trainParams["dataFileName"],
            "modelPath":trainParams["modelPath"],
            "modelName":"DartsTFT",
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
            "parameters" : {"n_epochs": trial.suggest_int('n_epochs', 10, 40,step=10), 
                            "dropout":trial.suggest_float('dropout', 0.1, 0.5,step=0.1),
                            "num_attention_heads":trial.suggest_int('num_attention_heads', 1, 5),
                            "hidden_size":trial.suggest_int('hidden_size', 16,64),
                            "lstm_layers":trial.suggest_int('lstm_layers', 1, 3),
                            "batch_size":trial.suggest_int('lstm_layers', 32,96,step=32),
                            "add_relative_index":False,
                            "random_state":0, 
                            "verbose":False,
                            "hidden_continuous_size":29, 
                            "lr": 0.014454397707459274},
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

        model = DartsTFT(params)

        status = TRAINING_HYPER_PARAMETER_TUNING
        update_training_status(AMLRunId,status,total_epoch,-1,n_trials,trial.number,ChildAMLRunId,None)
        modelFilePath = model.trainModel()

        status = TESTING_HYPER_PARAMETER_TUNING
        update_training_status(AMLRunId,status,total_epoch,-1,n_trials,trial.number,ChildAMLRunId,None)
        rmse = model.testModel()

        status = FINISHING_HYPER_PARAMETER_TUNING
        update_training_status(AMLRunId,status,total_epoch,-1,n_trials,trial.number,ChildAMLRunId,None)
        
        return rmse