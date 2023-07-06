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

from darts import TimeSeries

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

        modelFolder = ds.download(target_path="../", prefix=modelPath+modelName) #outputs/
        dataPath = ds.download(target_path="./", prefix=dataFolderName+sourceFileName)
        inputdata = pd.read_csv("./"+dataFolderName+sourceFileName)

        model_path = "../"+modelPath+modelName+"/"+modelName+".pkl"
        
        data = []
        with open(model_path, 'rb') as f:
            while True:
                try:
                    data.append(pickle.load(f))
                except EOFError:
                    break
        model = data[1]
        trainer = data[0]
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
        }
        fp = scoring_config.get("parameters").get(modelName)
        forecast_params = {**forecast_params, **fp} 

        logging.info("Model scoring: request received")

        # Prepare past covariates data (Past and known covariates)
        data = data.fillna(0)
        data_df = data.assign(datehour=data[forecast_params["dateField"]])
        data_df = data_df.reset_index(drop=True)
        data_df = data_df.set_index('datehour')
        data_df = data_df.reset_index(drop=False)
        cov_df = data_df.copy()
        pastCovariatesData = TimeSeries.from_dataframe(cov_df, 'datehour', forecast_params["requiredColumns"]) 
        futureCovariatesData = TimeSeries.from_dataframe(cov_df, 'datehour', forecast_params["futureCovariates"])
        #============================================================================================
        logging.info("Starting prediction")
        # Run prediction
        if not data.empty:
            # Preprocess data
            n = len(pastCovariatesData)-forecast_params["forecast_horizon"]
            if modelName == "DartsTFT": #Specific for algorithms needing future covariates
                predSeries = model.predict(n=n, past_covariates=pastCovariatesData,
                                                future_covariates=futureCovariatesData,
                                                n_jobs = -1, # Use all cores for processing prediction
                                                trainer = trainer,
                                                verbose=forecast_params["verbose"]
                                                )
            else:
                predSeries = model.predict(n=n, past_covariates=pastCovariatesData,
                                                n_jobs = -1, # Use all cores for processing prediction
                                                trainer = trainer,
                                                verbose=forecast_params["verbose"]
                                                )
        else:
            n = forecast_params["n"]
            predSeries = model.predict(n=n, trainer = trainer,verbose=forecast_params["verbose"])

        
        logging.info("Request processed")
        predSeries = predSeries.pd_dataframe()
        # If Error analysis is enabled

        if not os.path.isdir("score"):
            os.mkdir("score") 
        predSeries.to_csv("score/dartsprediction.csv")    
        #  ===============Upload the folder to the workspace's default data store ===============
        ds.upload('score/', target_path="scores/"+modelPath+modelName, overwrite=True)

        return predSeries
    except Exception as ex:
        logging.error("Error in model prediction.")
        logging.error(ex)
        raise ex

if __name__ == '__main__':
    init()