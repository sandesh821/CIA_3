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
import sys
import inspect

from azureml.core import Workspace
from azureml.core import Run

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
sys.path.insert(0, currentdir) 

from TFT import TFT
from ErrorAnalysis import executeMain

def init(config):
    logging.info("Initializing")
    """
    This function is called when the container is initialized/started, typically after create/update of the deployment.
    You can write the logic here to perform init operations like caching the model in memory
    """
    global scoring_config

    scoring_config = config

    logging.info("Init complete")

def run(data):
    try:
        path = os.getcwd()
        directory = os.path.dirname(path)
        
        modelName = scoring_config.get("modelName")
        modelPath = "src/model/"+scoring_config.get("modelPath")
        multiplicationFactorDict = {"H":1, "min" : (60), "S" : (60*60)}
        
        #Load model
        modeldata = []
        with open(directory + "/" + modelPath+modelName+"/"+modelName+".pkl", 'rb') as f:
            modeldata = pickle.load(f)
        model = modeldata

        forecast_params = {
            "modelPath": directory + "/" + modelPath
            ,"dateField" : scoring_config.get("dateField")
            ,"requiredColumns" : scoring_config.get("requiredColumns")
            ,"futureCovariates": scoring_config.get("futureCovariates")
            ,"targetColumn": scoring_config.get("targetColumn")
        }
        fp = scoring_config.get("parameters").get(modelName)
        forecast_params = {**forecast_params, **fp} 
        
        logging.info("TFT: Prediction request received")
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
        data_df = data_df[finalColumns]
        print(data_df)
        
        #============================================================================================
        logging.info("Starting prediction")
        # Run prediction
        if not data_df.empty:
            predSeries = TFT.predict(model,data_df,forecast_params)

        logging.info("Request processed")

        return predSeries
    except Exception as ex:
        logging.error("Error in model prediction.")
        logging.error(ex)
        raise ex