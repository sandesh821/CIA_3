#Copyright (c) Microsoft. All rights reserved.
import pandas as pd
import sys
from pathlib import Path
import os
import sys 
parent_dir = os.path.abspath(os.path.join(os.getcwd(), '..' , '..','..')) 
sys.path.append(parent_dir)
from utilities.azure.blobOperations import getBlobDf
from utilities.dboperations.dboperations import executeStoredProcedure
import json

class ModelDrift:
    def __init__(self,threshold,config):
        self.config=config
        self.train=getBlobDf(self.config['storage_acc_name'],self.config['container_name'],self.config['Training_file_name'])[1]
        self.test=getBlobDf(self.config['storage_acc_name'],self.config['container_name'],self.config['Testing_file_name'])[1]
        self.threshold = threshold
        self.predCol = 'Prediction'
        self.actualCol = 'Actual'
        self.drift_json=self.rmse()
        self.rmse()

    def rmse(self):
        train_df= self.train[[ self.predCol,self.actualCol]]
        test_df= self.test[[ self.predCol,self.actualCol]]
        actual=((train_df[self.predCol] - train_df[self.actualCol]) ** 2).mean() ** .5
        prediction=((test_df[self.predCol] - test_df[self.actualCol]) ** 2).mean() ** .5
        if (prediction - actual) > self.threshold :
            drift = 'True'
            drift_df=pd.DataFrame([[f'{drift}']],columns=['ModelDrift'])
            drift_json = drift_df.to_json(orient="columns")   
        else :
            drift = 'False'
            drift_df=pd.DataFrame([[f'{drift}']],columns=['ModelDrift'])
            drift_json = drift_df.to_json(orient="columns")
        return drift_json


if __name__ == '__main__':
    
    config = {
        'storage_acc_name': "devteamamlsa",
        'container_name': "dataset",
        'Training_file_name': 'TFT_valREsults.csv',
        'Testing_file_name':"test_data.csv",
        #'threshold' = 0.1
    }
    # cal_rmse=ModelDrift(threshold = 0.5,config=config)
    # cal_rmse.load()
    # cal_rmse.rmse()
    drift = ModelDrift(threshold = 0.5, config=config)
    executeStoredProcedure(procName="usp_InsertModelDriftAnalysisMetrics", paramList='@ModelDrift = ?', params=(str(drift.drift_json)), SchemaName="dbo", isGetResult=0)