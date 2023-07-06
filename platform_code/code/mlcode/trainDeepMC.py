#Copyright (c) Microsoft. All rights reserved.
from azureml.core import Run
import pandas as pd
import numpy as np
import os
import argparse
import datetime
import joblib
import logging
from azureml.core import Datastore
from azureml.core.model import Model
import yaml
import ast
import sys

from DeepMC import DeepMC
from HyperparameterTuning import optimize
from ErrorAnalysis import executeMain
from dboperations.dboperations import executeStoredProcedure
from prepareTrainingRun import *

from logUtils import get_AMLRunId, update_parent_training_run, update_training_status, get_ChildAMLRunId
from logConfig import PREPARE_TRAINING


# Parse input arguments
parser = argparse.ArgumentParser("split")
parser.add_argument("--modelName", type=str, required=True, help="Model Name")
parser.add_argument('--input', type=str, dest='model_input')
parser.add_argument('--output', type=str, dest='model_output')
parser.add_argument('--train_config', type=str, dest='train_config')
parser.add_argument('--preprocess_config', type=str, dest='preprocess_config')
parser.add_argument('--train_pipeline_config', type=str, dest='train_pipeline_config')
parser.add_argument('--dataFileName', type=str, dest='dataFileName')

args, _ = parser.parse_known_args()

train_config = ast.literal_eval(args.train_config) 
preprocess_config = ast.literal_eval(args.preprocess_config) 
train_pipeline_config = ast.literal_eval(args.train_pipeline_config) 

current_run = None

def init():
    global current_run
    current_run = Run.get_context()

    global masterParams
    masterParams = train_config
    
    #TRAINING PARAMETERS
    global trainParams
    trainParams=train_config["parameters"]

def run():
    init()

    modelName = args.modelName
    outputPath = args.model_output
    model_input = args.model_input

    # If AMLRunId exists, execute stored procedure
    AMLRunId = get_AMLRunId(modelPath=outputPath)
    ChildAMLRunId = get_ChildAMLRunId(modelPath=outputPath)

    createLog(current_run,outputPath,modelName)

    # ================Set up output directory and the results list=================
    if not os.path.isdir(outputPath):
        os.makedirs(outputPath)
    
    print("============Starting model training: ", modelName,"=============")
    # ===============Set the path of source file=====================
    trainingParameters = trainParams[modelName]
    trainingParameters["internalParams"] = trainParams[modelName+"internalParams"]
    trainingParameters["internalParams"]["isOptimizationEnabled"] = masterParams["isOptimizationEnabled"]
    
    # Prepare testing/validation parameters
    multiplicationFactorDict = {"H":1, "min" : (60), "S" : (60*60)}
    multiplicationFactor = multiplicationFactorDict.get(preprocess_config["frequency_duration"])

    masterParams["forecast_params"] = {
        "n" : preprocess_config["lookahead"], 
        "forecast_horizon": preprocess_config["lookback"],
        "freq": str(preprocess_config["frequency"])+preprocess_config["frequency_duration"],
        "verbose": True,
        "horizon" : preprocess_config["lookahead"],
        "targetColumn" : train_config["targetColumn"],
        "lookback" : preprocess_config["lookback"],
        "frequency" : preprocess_config["frequency"],
        "frequency_duration" : preprocess_config["frequency_duration"],
        "multiplicationFactor" : multiplicationFactor,
        "dateField" : train_config["dateField"],
        "quantileList" : train_config["quantileList"],
        "trunc" :  trainingParameters["trunc"]
    }
    
    masterParams["horizon"] = preprocess_config["lookahead"]
    masterParams["lookback"] = preprocess_config["lookback"]
    masterParams["freq"] = str(preprocess_config["frequency"])+preprocess_config["frequency_duration"]
    masterParams["frequency"] = preprocess_config["frequency"]
    masterParams["frequency_duration"] = preprocess_config["frequency_duration"]
    masterParams["multiplicationFactor"] = multiplicationFactor
    masterParams["datasetPath"] = model_input
    masterParams["modelName"] = modelName
    masterParams["modelPath"] = outputPath+"/"
    masterParams["forecast_params"]["modelPath"] = outputPath+"/"
    masterParams["forecast_params"]["modelType"] = modelName
    masterParams["dataFileName"] = args.dataFileName
    masterParams["parameters"] = trainingParameters
    masterParams["train_pipeline_config"] = train_pipeline_config
    
    # If AMLRunId exists, execute stored procedure
    update_training_status(AMLRunId,PREPARE_TRAINING,None,-1,None,None,ChildAMLRunId,masterParams["horizon"])

    #================================Invoke Model initialization, training and validation ====================
    try:
        modelClass = globals()[modelName]
        model = invokeModelTrainingAndValidation(modelClass,masterParams,outputPath,modelName)
    except Exception as ex:
        logging.error(ex)
        logging.info("Pipeline training failed")
        update_parent_training_run(outputPath,AMLRunId,"Failed")
        raise ex

        return "Failed"
    #  ===============Upload the folder to the workspace's default data store ===============
    saveOutputs(current_run,outputPath,modelName)

    # ===============Error Analysis======================
    if(masterParams["isErrorAnalysisEnabled"]):
        invokeErrorAnalysis(outputPath,modelName,masterParams)

    logging.info("Pipeline training finished")
    
    createLog(current_run,outputPath,modelName)
    
    update_parent_training_run(outputPath,AMLRunId,"Finished")
    
    return "Success"

run()