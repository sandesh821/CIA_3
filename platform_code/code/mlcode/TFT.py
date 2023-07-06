from BuildModel import BuildModel
import os
import time
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns; sns.set()

import tensorflow as tf
import tensorboard as tb
tf.io.gfile = tb.compat.tensorflow_stub.io.gfile

import warnings
warnings.filterwarnings('ignore')

import pytorch_lightning as pl
from pytorch_lightning.callbacks import EarlyStopping, LearningRateMonitor
from pytorch_lightning.loggers import TensorBoardLogger
import torch

from pytorch_forecasting import Baseline, TemporalFusionTransformer, TimeSeriesDataSet
from pytorch_forecasting.data import GroupNormalizer
from pytorch_forecasting.metrics import SMAPE, PoissonLoss, QuantileLoss
import logging
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
import ast

class TFT(BuildModel):
    def __init__(self,params):
        super().__init__(params)
        self.epochs = self.parameters.get("epochs")
        self.batch_size = self.parameters.get("batch_size")
        self.num_workers = params.get("num_workers",2)

        self.finalColumns = self.requiredColumns+[self.targetColumn]+self.futureCovariates+["time_idx",'Group']
        self.outputPath = self.modelPath

        self.quantilePrecList = self.parameters.get("quantileList")
        self.quantileList,self.lengthQuantileList,self.qunatiles,self.quantileNames = self.__quantileDetails__(self.quantilePrecList,self.parameters)
        self.__preprocess__()
        self.__prepareTrainDataLoader__()
    
    def __quantileDetails__(self,quantilePrecList,par):
        quantileList = [i/100 for i in quantilePrecList]
        quantileNames  = [str('p'+str(i)) for i in quantilePrecList]
        lengthQuantileList = len(quantilePrecList)
        if lengthQuantileList == 0 :
            qunatiles = [0.5]
        else: 
            qunatiles = quantileList
        return quantileList,lengthQuantileList,qunatiles,quantileNames


    def __generateDates__(start,end,freq):
        dates = pd.to_datetime(pd.date_range(start = str(start) , end = str(end) ,freq =freq))
        return dates

    def __buildTrainTestDataSet__(self):
        print("Start: Prepare Training and Validation dataset")
        # Split train and val data
        self.data = self.data[self.data.index<=str(self.val_end)]
        
        print(self.data.index.min(), self.data.index.max())
        
        data_df = self.data[self.finalColumns]
        self.train = data_df[data_df.index<=self.train_end]
        self.val = data_df[data_df.index>=self.val_start]
        
        self.train.reset_index(inplace=True)
        self.val.reset_index(inplace=True)
    
    def __preprocess__(self):
        # Parent's preprocessing method
        super().__preprocess__()
        
        self.data[self.dateField] = self.data.index
        self.data.reset_index(inplace = True)
        self.data["time_idx"] = self.data.index
        self.data['Group'] = ["grp"] * len(self.data)
        self.data.set_index(self.dateField, inplace=True)
        self.data = self.data[self.finalColumns]

        # Get Training dataset
        self.__buildTrainTestDataSet__()
        
    def __prepareTrainDataLoader__(self):

        print("Start: Preparing data loaders")
        self.training = TimeSeriesDataSet(
            data=self.train,
            time_idx= "time_idx",  # column name of time of observation
            target= self.targetColumn,  # column name of target to predict
            group_ids=["Group"],  # column name(s) for timeseries IDs
            max_encoder_length=self.lookback,  # how much history to use
            max_prediction_length=self.horizon,  # how far to predict into future
            allow_missing_timesteps=True,
            time_varying_unknown_reals=self.requiredColumns+[self.targetColumn],
            time_varying_known_reals =self.futureCovariates
        )
        self.validation = TimeSeriesDataSet.from_dataset(self.training, self.val, stop_randomization=True)
        
        self.train_dataloader = self.training.to_dataloader(train=True, batch_size=self.batch_size, num_workers=self.num_workers)
        self.val_dataloader = self.validation.to_dataloader(train=False, batch_size=self.batch_size, num_workers=self.num_workers)
        for (idx, batch) in iter(self.val_dataloader):
            print(batch[0],batch[1])

    def trainModel(self):
        # Hyperparameters
        parameters = self.parameters

        # create PyTorch Lighning Trainer with early stopping
        early_stop_callback = EarlyStopping(monitor="val_loss", min_delta=1e-4, patience=40, verbose=False, mode="min")
        lr_logger = LearningRateMonitor()
        # Fixing seed for reproductability
        random_seed = parameters["random_seed"]
        torch.manual_seed(random_seed)
        torch.cuda.manual_seed(random_seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
        np.random.seed(random_seed)

        params = self.modelName, self.modelPath
        
        AMLRunId = get_AMLRunId(modelPath=self.outputPath)
        ChildAMLRunId = get_ChildAMLRunId(modelPath=self.outputPath)
        print("inspect.stack()[1][3]", inspect.stack()[1][3])
        if 'objective' not in inspect.stack()[1]:
            update_training_status(AMLRunId,TRAINING_START,None,-1,None,None,ChildAMLRunId,None)

        # Check if the objective function is being called (i.e. if hyperparameter tuning is happening) if 'objective' is not inspect.stack()[1][3]
        # If not, add the update database callback with TorchTrainingLossDatabaseUpdateCallback(params)
        if 'objective' not in inspect.stack()[1]:
            # If not, add the database update callback
            callbacks=[lr_logger, early_stop_callback, TorchTrainingLossDatabaseUpdateCallback(params)]
        else:
            callbacks=[lr_logger, early_stop_callback]
            
        trainer = pl.Trainer(
            max_epochs=parameters["max_epochs"],
            # weights_summary="top",
            # gpus=1,  # run on CPU, if on multiple GPUs, use accelerator="ddp"
            gradient_clip_val=parameters["gradient_clip_val"],
            limit_train_batches=30,  # 30 batches per epoch
            callbacks=callbacks,
            logger=TensorBoardLogger("lightning_logs")
        )

        # define network to train - the architecture is mostly inferred from the dataset, so that only a few hyperparameters have to be set by the user
        tft = TemporalFusionTransformer.from_dataset(
            # dataset
            self.training,
            # architecture hyperparameters
            hidden_size=parameters['hidden_size'],
            attention_head_size=parameters["attention_head_size"],
            dropout=parameters['dropout'],
            hidden_continuous_size=parameters["hidden_continuous_size"],
            # loss metric to optimize
            loss=QuantileLoss(quantiles = self.quantileList),
            #output_size = self.lengthQuantileList
            # logging frequency
            log_interval=2,
            # optimizer parameters
            learning_rate=parameters["learning_rate"],
            reduce_on_plateau_patience=10
        )

        trainer.fit(
            tft, train_dataloaders=self.train_dataloader, val_dataloaders=self.val_dataloader,
        )

        model_path = trainer.checkpoint_callback.best_model_path
        self.tft_model = TemporalFusionTransformer.load_from_checkpoint(model_path)
        
        # Save model as pickle file
        self.__saveModel__(self.tft_model,"TFT")

        print("Model training complete")
        if 'objective' not in inspect.stack()[1]:
            update_training_status(AMLRunId,TRAINING_END,None,-1,None,None,ChildAMLRunId,None)

        return self.modelFilePath

    def __get_val__(df_power2,horizon):
        dates, preds = [], []
        count = 0
        for index, row in df_power2.iterrows():
            if index % horizon == 0:
                all_preds = [row['P_'+str(ii)] for ii in range(0,horizon)]
                preds.extend(all_preds[:])                
                count += 1
        return preds
    
    def createdict(self,valu):
        dictvalue = {}
        for k,v in enumerate(valu.index) : 
            dictvalue[v] = valu[k]
        return dictvalue

    def testModel(self):
        quantileLength =  self.lengthQuantileList
        # calcualte mean absolute error on validation set
        self.actuals = torch.cat([y[0] for x, y in iter(self.val_dataloader)])
        self.predictions = self.tft_model.predict(self.val_dataloader  ,mode = 'quantiles')
        shapeValue = self.predictions.shape[0]
        k = self.predictions.reshape([shapeValue, self.horizon * quantileLength])
        cols = ["P_" + str(i) for i in range(0,self.horizon * quantileLength)]
        col = ["P_" + str(i) for i in range(0,self.horizon)]
        df = pd.DataFrame(k, columns=cols).astype(float)
        df_2  = pd.DataFrame()
        df_flat = pd.DataFrame()
        for j in range (0,quantileLength) :
            df_2 = pd.DataFrame()
            for i in range(j,self.horizon * quantileLength,quantileLength):
                print(i)
                df_2 = pd.concat([df_2,df[f'P_{i}']],axis = 1 )
            df_2.columns = col
            df_flat[f'p{j}'] = TFT.__get_val__(df_2,self.horizon)
        df_flat.columns = self.quantileNames
        result = pd.DataFrame()
        result['Prediction'] = df_flat['p50'].values
        
        quantileDF = pd.DataFrame()
        for percentile in self.quantileNames :
            quantileDF[percentile] = df_flat[percentile].values
        quantileDF['Quantile']  = quantileDF.apply(self.createdict,axis = 1)
        result['Quantile'] = quantileDF['Quantile']
        actual_cols = ["P_" + str(i) for i in range(0,self.horizon)]
        result['Actual'] = TFT.__get_val__(pd.DataFrame(self.actuals, columns=actual_cols).astype(float),self.horizon)
        dates = TFT.__generateDates__(self.val_start,self.val_end,self.freq)[:len(result['Actual'])]
        result['DateTime'] = dates

        self.__saveValData__(result,self.modelName)
        try:
            # Get RMSE score
            rmse = self.__rmse__(result)
        except Exception as ex:
            logging.error("Error in validation")

        self.result = pd.DataFrame([[self.modelName,self.requiredColumns,self.futureCovariates,self.lookback,self.horizon,rmse]],columns=['Model',"Past Covariates","Future Covariates","Lookback","Horizon",'RMSE'])

        return rmse

    def predict(model,data,params):

        def createdict(valu):
            dictvalue = {}
            for k,v in enumerate(valu.index) : 
                dictvalue[v] = valu[k]
            return dictvalue
        
        lookback = params["lookback"]
        lookahead = params["forecast_horizon"]
        frequency = params["frequency"]
        frequency_duration = params["frequency_duration"]
        quantileList = params["quantileList"]
        quantileNames = [str('p'+str(i)) for i in quantileList]
        quantileLength = len(quantileList)
    
        # Get the date list for prediction
        try:
            start = data.index[lookback]
            end = data.index[-(lookahead)]
            print(start,end)
            preddates = TFT.__generateDates__(start,end,str(lookahead*frequency)+frequency_duration)
            if(len(preddates)==0):
                raise Exception("Data doesn't have enough past and future values")
        except Exception as ex:
            print(ex)
            raise ex

        preddates = preddates.strftime("%Y-%m-%d %H:%M:%S").tolist()
        result = pd.DataFrame()
        preds = []
        preds_df = pd.DataFrame()
        for date in preddates:
            dateIndex = data.index.get_loc(date)
            startIndex = dateIndex-lookback
            endIndex = dateIndex+lookahead
            predData = data[startIndex:endIndex]
            predSeries = model.predict(predData,mode = 'quantiles')

            shapeValue = predSeries.shape[0]
            k = predSeries.reshape([shapeValue, lookahead*quantileLength])
            cols = ["P_" + str(i) for i in range(0,lookahead*quantileLength)]
            col = ["P_" + str(i) for i in range(0,lookahead)]
            df = pd.DataFrame(k, columns=cols).astype(float)
            df_2  = pd.DataFrame()
            df_flat = pd.DataFrame()
            for j in range (0,quantileLength) :
                df_2 = pd.DataFrame()
                for i in range(j,lookahead*quantileLength,quantileLength):
                    df_2 = pd.concat([df_2,df[f'P_{i}']],axis = 1 )
                df_2.columns = col
                df_flat[f'p{j}'] = TFT.__get_val__(df_2,lookahead)
            df_flat.columns = quantileNames
            result = pd.DataFrame()
            result['Prediction'] = df_flat['p50'].values

            quantileDF = pd.DataFrame()
            for percentile in quantileNames :
                quantileDF[percentile] = df_flat[percentile].values

            quantileDF['Quantile']  = quantileDF.apply(createdict,axis = 1)
            result['Quantile'] = quantileDF['Quantile']
            preds_df = pd.concat([preds_df,result],axis = 0 )
        dates = TFT.__generateDates__(data.index.min(),predData.index.max(),str(frequency)+frequency_duration)[lookback:]
        preds_df['DateTime'] = dates
        preds_df.index = pd.to_datetime(preds_df['DateTime'])
        return preds_df

    def prepareValResults(predictions,inputData,params=None):
  
        predictions.index = pd.to_datetime(predictions.index)
        inputData.index = pd.to_datetime(inputData.index)        
        outputData = predictions.merge(inputData,how = 'inner', left_index=True, right_index=True) 
        print(params)
        outputData.rename(columns={params.get("targetColumn",""):"Actual"},inplace=True)

        if(params is not None and params.get("descalingEnabled")):
            descalingColumn = params.get("descalingColumn")
            numberOfTurbines = params.get("numberOfTurbines")
            outputData['Actual'] = (outputData[descalingColumn]/numberOfTurbines)*outputData["Actual"]
            outputData['Prediction'] = (outputData[descalingColumn]/numberOfTurbines)*outputData["Prediction"]

        return outputData

    def objective(trial,datasetPath,trainParams,n_trials):
        print(trainParams)
        params ={
                "datasetPath":datasetPath,
                "dataFileName":trainParams["dataFileName"],
                "modelPath":trainParams["modelPath"],
                "modelName":"TFT",
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
                "parameters" : {"quantileList" : trainParams["parameters"]['TFT']['quantileList'],
                            "random_seed":trial.suggest_int('random_seed', 1,3),
                            'max_epochs':trial.suggest_int('max_epochs', 10, 30,step=10),
                            'gradient_clip_val': trial.suggest_float('gradient_clip_val', 0.01, 1.0,step=0.1), 
                            'hidden_size': trial.suggest_int('hidden_size', 8, 128), 
                            'dropout': trial.suggest_float('dropout', 0.1, 0.3,step=0.1), 
                            'hidden_continuous_size': trial.suggest_int('hidden_continuous_size', 10, 25),
                            'attention_head_size': trial.suggest_int('attention_head_size', 1, 4),
                            'learning_rate': trial.suggest_float('learning_rate', 0.001, 0.9,step=0.1),
                            "batch_size": trial.suggest_int('batch_size', 32, 64,step=32)},
                "forecast_params" : {}
                
            } 

        # retrieves the file path of the model being trained
        modelPath = params['modelPath']
        # retrieves the AML run ID associated with the model
        AMLRunId = get_AMLRunId(modelPath=modelPath)
        ChildAMLRunId = get_ChildAMLRunId(modelPath=modelPath)
        # calculate the total epoch completed
        total_epoch = params['parameters']['max_epochs']


        # update the status of the trial, first to "running", then to "training", then to "testing", and finally to "finished".
        
        status = RUNNING_HYPER_PARAMETER_TUNING
        update_training_status(AMLRunId,status,total_epoch,-1,n_trials,trial.number,ChildAMLRunId,None)

        model = TFT(params)

        status = TRAINING_HYPER_PARAMETER_TUNING
        update_training_status(AMLRunId,status,total_epoch,-1,n_trials,trial.number,ChildAMLRunId,None)
        modelFilePath = model.trainModel()

        status = TESTING_HYPER_PARAMETER_TUNING
        update_training_status(AMLRunId,status,total_epoch,-1,n_trials,trial.number,ChildAMLRunId,None)
        rmse = model.testModel()

        status =FINISHING_HYPER_PARAMETER_TUNING
        update_training_status(AMLRunId,status,total_epoch,-1,n_trials,trial.number,ChildAMLRunId,None)
        
        return rmse