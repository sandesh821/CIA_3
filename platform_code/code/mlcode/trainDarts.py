#Copyright (c) Microsoft. All rights reserved.
import os
import argparse
import datetime
import logging
import yaml
import ast
import json
from azureml.core import Run
from azureml.core.model import Model
import gc
import pathlib

from DartsTCN import DartsTCN
from DartsNBeats import DartsNBeats
from DartsTFT import DartsTFT
from prepareTrainingRun import *

from dboperations.dboperations import executeStoredProcedure
from logUtils import get_AMLRunId, update_parent_training_run, update_training_status, get_ChildAMLRunId
from logConfig import PREPARE_TRAINING


# Parse input arguments
parser = argparse.ArgumentParser("split")
parser.add_argument("--modelName", type=str, required=True, help="Model Name")
parser.add_argument('--input', type=str, dest='model_input')
parser.add_argument('--output', type=str, dest='model_output')
parser.add_argument('--train_config', type=str, dest='train_config')
parser.add_argument('--preprocess_config', type=str, dest='preprocess_config')
parser.add_argument('--dataFileName', type=str, dest='dataFileName')

args, _ = parser.parse_known_args()

train_config = ast.literal_eval(args.train_config) 
preprocess_config = ast.literal_eval(args.preprocess_config) 

current_run = None

def init():
    global current_run
    current_run = Run.get_context()

    global masterParams

    masterParams = train_config
    masterParams["forecast_params"] = {
        "n" : preprocess_config["lookahead"], # This will be used in Darts in case of future coavariates only
        "forecast_horizon": preprocess_config["lookback"],
        "freq": str(preprocess_config["frequency"])+preprocess_config["frequency_duration"],
        "verbose": True
    }
    
def run():
    init()

    modelName = args.modelName
    outputPath = args.model_output
    model_input = args.model_input

    # If AMLRunId exists, execute stored procedure
    AMLRunId = get_AMLRunId(modelPath=outputPath)
    ChildAMLRunId = get_ChildAMLRunId(modelPath=outputPath)
    # If AMLRunId exists, execute stored procedure
    update_training_status(AMLRunId,PREPARE_TRAINING,None,-1,None,None,ChildAMLRunId,None)
    createLog(current_run,outputPath,modelName)
    
    try:
        runTrain(args,masterParams,preprocess_config,globals()[modelName])

        saveOutputs(current_run,outputPath,modelName)
    except Exception as ex:
        logging.error(ex)
        logging.info("Pipeline training failed")
        update_parent_training_run(outputPath,AMLRunId,"Failed")
        raise ex
    
    createLog(current_run,outputPath,modelName)
    update_parent_training_run(outputPath,AMLRunId,"Finished")

    #  ===============Register the model  ===============
    ws = current_run.experiment.workspace
    model = Model.register(ws,model_name=modelName, model_path=outputPath+'/'+modelName+"/"+modelName+'.pkl')
    print(model.name, model.id, model.version, sep='\t')

    gc.collect()
    return "Success"

run()