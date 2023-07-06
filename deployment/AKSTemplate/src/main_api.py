import warnings
warnings.filterwarnings("ignore", category=UserWarning)

import os
import sys
import inspect

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir) 

from src.code.mlcode.$$scorescript$$ import init,run
import pandas as pd
from fastapi import FastAPI, Request
import logging
import yaml
import ast
import logging
import json
app = FastAPI()

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

@app.get("/")
def default():
    return "API loaded"

@app.post("/input")
async def input_request(request: Request):
    data = await request.body()
    data = json.loads(data)
    return data["data"]

@app.post("/predict")
async def main(request: Request):
    data = await request.body()
    data = json.loads(data)
    data = data["data"]
    data = pd.read_json(data, orient="records")
    init(scoring_config_parsed)
    
    pred_result = run(data)

    return pred_result.to_dict("records")