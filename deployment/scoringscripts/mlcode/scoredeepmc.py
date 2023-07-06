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

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
sys.path.insert(0, currentdir) 

# from darts import TimeSeries
from DeepMC import DeepMC

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

        # Prepare past covariates data (Past and known covariates)
        data = data.fillna(0)
        data_df = data.assign(datehour=data[forecast_params["dateField"]])
        data_df = data_df.reset_index(drop=True)
        data_df = data_df.set_index('datehour')
        data_df = data_df[forecast_params["requiredColumns"]+[forecast_params["targetColumn"]]+forecast_params["futureCovariates"]+[originalDateColumnName]]

        # print commands just for testing (TODO: remove after testing)
        print(data_df[-48:])
        try:
            data_df[forecast_params["futureCovariates"]] = data_df[forecast_params["futureCovariates"]].shift(-1 * forecast_params["horizon"])
        except Exception as ShiftIndexError:
            logging.error('Error occured while shifting the data for DeepMC data')
            raise ShiftIndexError
        print(data_df[-48:])
        #------------------------
        predSeries = DeepMC.predict(forecast_params,data_df) 

        return predSeries
    except Exception as ex:
        logging.error("Error in model prediction.")
        logging.error(ex)
        raise ex