#Copyright (c) Microsoft. All rights reserved.
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import logging
import pandas as pd
import os
import numpy as np
from FeatureEngineeringUtils import *
import datetime
import pickle
import bz2
# import faulthandler
# faulthandler.enable()

'''
Master class for Model building, training, testing and getting forecasts
'''
class BuildModel(object):
    def __init__(self,params):
        self.datasetPath = params["datasetPath"]
        self.dataFileName = params["dataFileName"]
        self.modelPath = params["modelPath"]
        self.freq = params["freq"]
        self.requiredColumns = params["requiredColumns"]
        self.targetColumn = params["targetColumn"]
        self.parameters = params["parameters"]
        self.dateField = params["dateField"]
        self.modelName = params["modelName"]
        self.futureCovariates = params["futureCovariates"] if params["futureCovariates"] else []
        self.train_end = params["train_end"]  # between train and validation
        self.val_end = params["val_end"]  # between validation and test
        self.val_start = params["val_start"]  
        self.horizon = params["horizon"] #lookahead
        self.lookback = params["lookback"] #lookback
        self.forecast_params = params["forecast_params"]
        self.frequency = params["frequency"]
        self.frequency_duration = params["frequency_duration"]
        self.multiplicationFactor = params["multiplicationFactor"]
        
    # Read dataset as CSV
    def __readDataset__(self):
        try:
            logging.info("Start: Load dataset")
            self.data = pd.read_csv(self.datasetPath+"/"+self.dataFileName+"/"+self.dataFileName+".csv")

            folderPath = self.modelPath+self.modelName+"/sourcedata/"
            if(not os.path.exists(folderPath)):
                os.makedirs(folderPath)
            self.data.to_csv(folderPath+self.dataFileName+".csv")
            
            logging.info("End: Load dataset")
        except Exception as ex:
            logging.error("Error loading source file.")
            logging.error(ex)
            raise ex

    # Add preprocess for missing values and 
    def __preprocess__(self):
        logging.info("Start: Preprocess dataset")
        self.__readDataset__()
        originalDateFieldName = self.dateField+"Original"
        data_df = self.data.assign(datehour=self.data[self.dateField])
        data_df = data_df.reset_index(drop=True)
        data_df = data_df.set_index('datehour')
        # Select subset of data
        data_df = data_df[self.requiredColumns+[self.targetColumn]+self.futureCovariates+[originalDateFieldName]]
        self.data = data_df
        
        # Map the dates to reindexed dates
        data_df[originalDateFieldName] = pd.to_datetime(data_df[originalDateFieldName])
        self.train_end = pd.to_datetime(self.train_end)
        
        self.train_end = data_df[data_df[originalDateFieldName]<=self.train_end].index.max()
        self.val_start = data_df[data_df[originalDateFieldName]>=self.val_start].index.min()
        self.val_end = data_df[data_df[originalDateFieldName]<=self.val_end].index.max()
        
        print(self.train_end)
        print(self.val_start)
        print(self.val_end)

        dfLen = len(data_df[data_df[originalDateFieldName]<=self.val_end]) + self.horizon
        data_df = data_df[:dfLen]

        logging.info("End: Preprocess dataset")

    def __rmse__(self,result):
        return np.sqrt(np.mean(list((result['Prediction'] - result['Actual'])**2)))

    def __saveModel__(self,data,modelName):
        try:
            print("Saving ",modelName)
            folderName = modelName.split("_")[0]
            if(not os.path.exists(self.modelPath+folderName)):
                os.makedirs(self.modelPath+folderName)
            self.modelFilePath = self.modelPath+folderName+"/"+modelName+".pkl"
            if folderName == "DeepMC" and "final" not in modelName:
                print("Saving Optimized file")
                # Save optimized
                ofile = bz2.BZ2File(self.modelFilePath,'wb')
                pickle.dump(data,ofile)
                ofile.close()
            elif "Darts" in modelName or "final" in modelName:
                print("Splitting data list")
                with open(self.modelFilePath, 'wb') as f:
                    for d in data:
                        pickle.dump(d, f)
            else:
                with open(self.modelFilePath, 'wb') as f:
                    pickle.dump(data, f)
                print("Saved pickle file")
            # Save model
            logging.info("=========Model Saved=========")
            return self.modelFilePath
        except Exception as ex:
            logging.error("Error while saving model.")
            logging.error(ex)
            raise ex
    
    def __saveValData__(self,data,modelName):
        try:
            logging.info("=========Start: Extract Validation Data=========")
            folderName = modelName.split("_")[0]
            if(not os.path.exists(self.modelPath+folderName)):
                os.makedirs(self.modelPath+folderName)
            valFilePath = self.modelPath+folderName+"/"+modelName+"_valResults.csv"
            data.to_csv(valFilePath)
            # Save model
            logging.info("=========End: Extract Validation Data=========")
            return self.modelFilePath
        except Exception as ex:
            logging.error("Error while saving model.")
            logging.error(ex)

    def __loadModel__(self,modelFilePath):
        data = []
        with open(modelFilePath, 'rb') as f:
            while True:
                try:
                    data.append(pickle.load(f))
                except EOFError:
                    break
        return data
    
    def printResults(self):
        try:
            print(self.result)
            return self.result
        except AttributeError as ex:
            logging.error("Pipeline failed, results not generated")
            logging.error(ex)
            return None
        