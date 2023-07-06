#Copyright (c) Microsoft. All rights reserved.
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

from BuildModel import BuildModel
import pandas as pd
import logging
from darts import TimeSeries
from typing import List, Tuple, Dict
from darts.metrics.metrics import rmse, smape
from darts.utils.losses import SmapeLoss
import numpy as np
from FeatureEngineeringUtils import *
import matplotlib.pyplot as plt
import gc

class DARTS(BuildModel):
    def __init__(self,params):
        super().__init__(params)

    def __preprocessData__(self):
        super().__preprocess__()
        try:
            # Split train data and convert it into timeseries
            data_df = self.data.reset_index(drop=False)
            
            # Scale and prepare the target series
            # Target series for training
            self.dataPreprocessedData = TimeSeries.from_dataframe(data_df, 'datehour', [self.targetColumn])

            # Prepare past covariates data (Past and known covariates)
            cov_df = data_df.copy()
            self.dataPreprocessedCovariatesData = TimeSeries.from_dataframe(cov_df, 'datehour', self.requiredColumns)        
            
            # Prepare future covariates
            if(self.futureCovariates and len(self.futureCovariates)):
                self.dataPreprocessedFutureCovariates = TimeSeries.from_dataframe(cov_df, 'datehour', self.futureCovariates)

        except Exception as ex:
            
            logging.error("Error encountered in preprocessing.")
            logging.error(ex)

    def __buildTrainTestDataSet__(self):
        try:
            # Filter data beyond validation end datetime
            self.dataPreprocessedData, test = self.dataPreprocessedData.split_after(pd.Timestamp(self.val_end))
            self.dataPreprocessedCovariatesData, test = self.dataPreprocessedCovariatesData.split_after(pd.Timestamp(self.val_end))
            
            #Prepare entity data
            
            if(self.train_end == self.val_end):
                self.train = self.dataPreprocessedData
                self.validat = None

                self.train_cov = self.dataPreprocessedCovariatesData
                self.val_cov = None
            else:
                self.train, self.validat = self.dataPreprocessedData.split_after(pd.Timestamp(self.train_end))
                # Prepare past covariates data
                self.train_cov, self.val_cov = self.dataPreprocessedCovariatesData.split_after(pd.Timestamp(self.train_end))

            if(self.futureCovariates and len(self.futureCovariates)):
                self.dataPreprocessedFutureCovariates,test = self.dataPreprocessedFutureCovariates.split_after(pd.Timestamp(self.val_end))
                #Prepare future covariates
                if(self.train_end == self.val_end):
                    self.train_fut_cov = self.dataPreprocessedFutureCovariates
                    self.val_fut_cov = None
                elif(self.futureCovariates and len(self.futureCovariates)):
                    self.train_fut_cov, self.val_fut_cov = self.dataPreprocessedFutureCovariates.split_after(pd.Timestamp(self.train_end))
                else:
                    self.train_fut_cov = None
                    self.val_fut_cov = None
            
            del test
            gc.collect()
                
        except Exception as ex:
            logging.error("Error while splitting dataset.")
            logging.error(ex)
            raise ex

    def __rmse__(self):
        try:
            logging.info("==========Calculation RMSE score=========")
            pred = self.predSeries
            pred = pred[0]
            pred_start_time = pred.start_time()
            pred_start_time = pred_start_time.to_pydatetime()
            pred_start_time = pred_start_time + timedelta(seconds=-self.frequency*(3600/self.multiplicationFactor))    
            test_series = self.dataPreprocessedData.drop_before(pd.Timestamp(pred_start_time))
            pred_df = self.predSeries.pd_dataframe()
            test_df = test_series.pd_dataframe()

            pred_df = pred_df.rename(columns={"0":"Prediction"})
            test_df = test_df.rename(columns={self.targetColumn:"Actual"})
            self.valData  = pd.merge(test_df,pred_df, left_index=True, right_index=True)
            data_df = self.data
            data_df.index = pd.to_datetime(data_df.index)

            self.valData  = pd.merge(self.valData,self.data,left_index=True, right_index=True)

            score = rmse(self.predSeries,test_series)
            self.result = pd.DataFrame([[self.modelType,self.requiredColumns,self.futureCovariates,self.lookback,self.horizon,score]],columns=['Model',"Past Covariates","Future Covariates","Lookback","Horizon",'RMSE'])
            return score
        except Exception as ex:
            logging.error("Error while calculating RMSE score.")
            logging.error(ex)
            raise ex

    def predict(self,modelFilePath,forecast_params,data=None):
        logging.info("Start: Model Prediction")
        logging.info("Load model from file")
        data = []
        with open(modelFilePath, 'rb') as f:
            while True:
                try:
                    data.append(pickle.load(f))
                except EOFError:
                    break
        model = data[1]
        trainer = data[0]
        
        if data:
            # TODO: Scale the past covariates
            n = len(data) - self.horizon

            predSeries = model.predict(n=n, 
                                            past_covariates=data,
                                            n_jobs = -1, # Use all cores for processing prediction
                                            trainer = trainer,
                                            verbose=self.forecast_params["verbose"]
                                            )
        else:
            n = forecast_params["n"]

            predSeries = model.predict(n=n, 
                                            trainer = trainer,
                                            verbose=forecast_params["verbose"]
                                            )

        logging.info("End: Model Prediction, prediction series generated successfully")
        # TODO: Inverse transform the predictions
        return predSeries.pd_dataframe()