#Copyright (c) Microsoft. All rights reserved.
import os
import logging
import numba
import json
import numpy
import pickle
import pandas as pd
import sys
import inspect
import argparse
import yaml
import ast

from azureml.core import Workspace
from azureml.core.model import Model
from azureml.core import Run

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir) 

# from darts import TimeSeries
from DeepMC import DeepMC

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
    global ws
    global ds

    try:
        # ws = Workspace.from_config()
        global current_run
        current_run = Run.get_context()
        ws = current_run.experiment.workspace
        ds = ws.get_default_datastore()

        #========================Prepare input dataset==================================
        prepareDataset(ws,scoring_config)
        
        #========================Download dataset===============================
        modelFolder = ds.download(target_path="../", prefix=modelPath+modelName) #outputs/
        dataPath = ds.download(target_path="./data/", prefix=dataFolderName+sourceFileName)
        inputdata = pd.read_csv("./data/"+dataFolderName+sourceFileName)

    except Exception as ex:
        logging.error("Error in data download.")
        logging.error(ex)    
        raise ex
        
    logging.info("Init complete")
    run(inputdata)


def run(data):
    #init()
    try:
        path = os.getcwd()
        directory = os.path.dirname(path)
        
        multiplicationFactorDict = {"H":1, "min" : (60), "S" : (60*60)}
        #=============================Prediction==========================
        forecast_params = {
            "modelPath": directory+"/"+modelPath
            ,"modelType" : modelName
            ,"targetColumn" : scoring_config.get("targetColumn")
            ,"dateField" : scoring_config.get("dateField")
            ,"requiredColumns" : scoring_config.get("requiredColumns")
            ,"futureCovariates": scoring_config.get("futureCovariates")
        }
        fp = scoring_config.get("parameters").get(modelName)
        forecast_params = {**forecast_params, **fp}
        originalDateColumnName = forecast_params["dateField"]+"Original"

        multiplicationFactor = multiplicationFactorDict.get(forecast_params["frequency_duration"])
        forecast_params["multiplicationFactor"] = multiplicationFactor

        logging.info("DeepMC: Prediction request received")

        # Prepare past covariates data (Past and known covariates)a
        data = data.fillna(0)
        data_df = data.assign(datehour=data[forecast_params["dateField"]])
        data_df = data_df.reset_index(drop=True)
        data_df = data_df.set_index('datehour')
        data_df_src = data_df.copy()
        data_df = data_df[forecast_params["requiredColumns"]+[forecast_params["targetColumn"]]+forecast_params["futureCovariates"]+[originalDateColumnName]]

        #------------------------
        predSeries = DeepMC.predict(forecast_params,data_df)

        if (scoring_config.get("isErrorAnalysisEnabled")):
            errorAnalysisParams = scoring_config.get("errorAnalysisConfig")
            filePath  = forecast_params["modelPath"]+forecast_params["modelType"]
            # Update errorAnalysisParams
            errorAnalysisParams["dateField"] = forecast_params["dateField"]
            errorAnalysisParams["frequency"] = forecast_params["frequency"]
            errorAnalysisParams["horizon"] = forecast_params["horizon"]
            errorAnalysisParams["targetColumn"] = forecast_params["targetColumn"]
            errorAnalysisParams["filePath"] = filePath
            errorAnalysisParams["modelType"] = forecast_params["modelType"]
            errorAnalysisParams["multiplicationFactor"] = multiplicationFactor
            
            if(scoring_config.get("descalingEnabled")):
                print("Starting descaling")
                errorAnalysisParams["descalingEnabled"] = scoring_config.get("descalingEnabled")
                errorAnalysisParams["descalingColumn"] = scoring_config.get("descalingColumn")
                errorAnalysisParams["numberOfTurbines"] = scoring_config.get("numberOfTurbines")
                
                DeepMC.prepareValResults(predSeries,data_df_src,errorAnalysisParams)
            else:   
                print("descaling disabled")
                DeepMC.prepareValResults(predSeries,data_df,errorAnalysisParams)
            
            # Upload Validation result file
            targetDSPath = modelPath.replace("outputs","scores")
            ds.upload("validate/", target_path=targetDSPath+modelName, overwrite=True)

            logging.info("Start: Model error analysis")

            dataStorePath = "validate"
            pred_col = 'Prediction'
            act_col = 'Actual'
            dat_col = originalDateColumnName
            units = '(MW)'

            executeMain(dataStorePath,targetDSPath,modelName,pred_col,act_col,dat_col,units)
            logging.info("End: Model error analysis")

        logging.info("Request processed")

        if not os.path.isdir("score"):
            os.makedirs("score") 
        predSeries.to_csv("score/deepmcprediction.csv")    
        #  ===============Upload the folder to the workspace's default data store ===============
        ds.upload('score/', target_path=targetDSPath+modelName, overwrite=True)

        return predSeries
    except Exception as ex:
        logging.error("Error in model prediction.")
        logging.error(ex)
        raise ex

if __name__ == '__main__':
    init()