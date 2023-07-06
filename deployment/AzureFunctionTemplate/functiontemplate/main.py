#Copyright (c) Microsoft. All rights reserved.
import warnings
warnings.filterwarnings("ignore", category=UserWarning)

import os
import sys
import inspect

# currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
# parentdir = os.path.dirname(currentdir)
# sys.path.insert(0, parentdir) 

# from code.mlcode.$$scorescript$$ import init,run
import pandas as pd
import yaml
import ast
import logging
import json

dir_abs_path = os.getcwd()
sys.path.insert(0, dir_abs_path)

from func_$$updatedexperimentname$$.readBlob import loadDataFromBlob
from code.mlcode.dboperations.dboperations import executeStoredProcedure

def readConfig():
    #===================Load configurations===================
    try:
        with open("./scoringconfig.yaml", 'r') as file:
            confg = yaml.safe_load(file)
    except (IOError, ValueError, EOFError, FileNotFoundError) as ex:
        logging.error("Config file not found")
        logging.error(ex)
        raise ex
    except Exception as YAMLFormatException:
        logging.error("Config file not found")
        logging.error(YAMLFormatException)
        raise YAMLFormatException
    scoring_config = str(confg.get('ScoringConfig',{}))
    scoring_config_parsed = ast.literal_eval(scoring_config)
    return scoring_config_parsed

def getPredDate(experimentSet):
    df = executeStoredProcedure("usp_getPredictionSchedule","@ExperimentSet=?", (experimentSet),"score",1)
    print(df)
    return df[0]

def getData(predDate):
    data = loadDataFromBlob($$storageaccount$$,$$containername$$,"$$experimentset$$/$$experimenttag$$")

def predict(data):
    data = json.loads(data)
    data = data["data"]
    data = pd.read_json(data, orient="records")
    init(scoring_config_parsed)
    
    pred_result = run(data)

    return pred_result.to_dict("records")