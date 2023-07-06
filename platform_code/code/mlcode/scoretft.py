#Copyright (c) Microsoft. All rights reserved.
import os
import logging
import numba
import json
import numpy
import pickle
import pandas as pd
import argparse
import yaml
import ast

from azureml.core import Workspace
from azureml.core import Run

from TFT import TFT
from ErrorAnalysis import executeMain
from batchScoringInput import prepareDataset

parser = argparse.ArgumentParser("split")
parser.add_argument('--scoring_config', type=str, dest='scoring_config')
args, _ = parser.parse_known_args()
scoring_config = ast.literal_eval(args.scoring_config)

modelName = scoring_config.get("modelName")
sourceFileName = scoring_config.get("sourceFileName")
modelPath = scoring_config.get("modelPath")
dataFolderName = scoring_config.get("dataFolderName")

def init():
    logging.info("Initializing")
    """
    This function is called when the container is initialized/started, typically after create/update of the deployment.
    You can write the logic here to perform init operations like caching the model in memory
    """
    global model
    global trainer
    
    global ws
    global ds
    global inputdata
    try:
        # ================Set up data directory =================
       
        # ws = Workspace.from_config()
        global current_run
        current_run = Run.get_context()
        ws = current_run.experiment.workspace
        
        ds = ws.get_default_datastore()
        
        #========================Prepare input dataset==================================
        prepareDataset(ws,scoring_config)

        modelFolder = ds.download(target_path="../", prefix=modelPath+modelName) #outputs/
        dataPath = ds.download(target_path="./", prefix=dataFolderName+sourceFileName)
        inputdata = pd.read_csv("./"+dataFolderName+sourceFileName)
        model_path = "../"+modelPath+modelName+"/"+modelName+".pkl"

        data = []
        with open(model_path, 'rb') as f:
            data = pickle.load(f)

        model = data
    except Exception as ex:
        logging.error("Error in model download and initialization.")
        logging.error(ex)
        raise ex
    logging.info("Init complete")
    run(inputdata)

def run(data):
    #init()
    try:

        forecast_params = {
            "modelPath": "outputs/"+modelPath
            ,"dateField" : scoring_config.get("dateField")
            ,"requiredColumns" : scoring_config.get("requiredColumns")
            ,"futureCovariates": scoring_config.get("futureCovariates")
            ,"targetColumn": scoring_config.get("targetColumn")
        }
        fp = scoring_config.get("parameters").get(modelName)
        forecast_params = {**forecast_params, **fp} 
        originalDateColumnName = forecast_params["dateField"]+"Original"
        
        logging.info("Model scoring: request received")
        finalColumns = forecast_params["requiredColumns"]+[forecast_params["targetColumn"]]+forecast_params["futureCovariates"]+["time_idx",'Group']

        # Prepare past covariates data (Past and known covariates)
        data_df = data.assign(datehour=data[forecast_params["dateField"]])
        data_df = data_df.reset_index(drop=True)
        data_df = data_df.set_index('datehour')
        
        dateField = forecast_params["dateField"]
        data[dateField] = data_df.index
        data_df.reset_index(inplace = True)
        data_df["time_idx"] = data_df.index
        data_df['Group'] = ["grp"] * len(data_df)
        data_df.set_index(dateField, inplace=True)
        testDataset = data_df
        data_df = data_df[finalColumns]
        #============================================================================================
        logging.info("Starting prediction")
        # Run prediction
        if not data_df.empty:
            predSeries = TFT.predict(model,data_df,forecast_params)

        logging.info("Request processed")

        targetDSPath = modelPath.replace("outputs","scores")

        if (scoring_config.get("isErrorAnalysisEnabled")):
            errorAnalysisParams = scoring_config.get("errorAnalysisConfig")
            
            if(scoring_config.get("descalingEnabled")):
                print("Starting descaling")
                forecast_params["descalingEnabled"] = scoring_config.get("descalingEnabled")
                forecast_params["descalingColumn"] = scoring_config.get("descalingColumn")
                forecast_params["numberOfTurbines"] = scoring_config.get("numberOfTurbines")
                
            valResults = TFT.prepareValResults(predSeries,testDataset,forecast_params)
    
            if not os.path.isdir("validate"):
                os.makedirs("validate") 
            valResults.to_csv("validate/"+modelName+"_valResults.csv")
            ds.upload("validate/", target_path=targetDSPath+modelName, overwrite=True)

            logging.info("Start: Model error analysis")

            dataStorePath = "validate"
            pred_col = 'Prediction'
            act_col = 'Actual'
            dat_col = originalDateColumnName
            units = '(MW)'

            executeMain(dataStorePath,targetDSPath,modelName,pred_col,act_col,dat_col,units)
            logging.info("End: Model error analysis")

        #  ===============Upload the folder to the workspace's default data store ===============
        if not os.path.isdir("score"):
            os.makedirs("score") 
        predSeries.to_csv("score/tftprediction.csv")
        ds.upload('score/', target_path=targetDSPath+modelName, overwrite=True)

        return predSeries
    except Exception as ex:
        logging.error("Error in model prediction.")
        logging.error(ex)
        raise ex

if __name__ == '__main__':
    init()