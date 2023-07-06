#Copyright (c) Microsoft. All rights reserved.
from azureml.core import Workspace
import pandas as pd
import yaml
import ast
import logging
import os
import argparse

from azureml.core import Dataset, Datastore


#===================Load configurations===================
try:
    with open("./src/scoringconfig.yaml", 'r') as file:
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
#===========================================================


ws = Workspace.from_config()
# Datastore
ds = ws.get_default_datastore()

# Temporary (load input data)
# dataset_input = Dataset.Tabular.from_delimited_files(path = [(ds,"outputs/experimentset1/experiment2/20230201181554/TFT/sourcedata/data.csv")],header='ALL_FILES_HAVE_SAME_HEADERS')

dataset_input = Dataset.Tabular.from_delimited_files(path = [(ds,"outputs/experimentset1/experiment1/20230202064548/DeepMC/sourcedata/deepmc_data.csv")],header='ALL_FILES_HAVE_SAME_HEADERS')

sample = dataset_input.to_pandas_dataframe()
# Clean missing values
sample = sample.set_index(pd.DatetimeIndex(sample["DateTime"]))

# DeepmC
startIndex = len(sample[sample["DateTimeOriginal"]>='2018-10-01 00:00:00']) + 512
endIndex = len(sample[sample["DateTimeOriginal"]<='2018-10-01 01:00:00']) + 24
score_input = sample[(len(sample) - startIndex): endIndex]

#TFT
# startIndex = len(sample[sample["DateTimeOriginal"]<'2018-09-25 00:00:00'])-24
# score_input = sample[startIndex:]
# endIndex = len(score_input[score_input["DateTimeOriginal"]<'2018-09-25 02:00:00'])+24
# score_input = score_input[:endIndex]

score_input = score_input.to_json(orient ="records", date_format='iso', date_unit = 's')
data = pd.read_json(score_input, orient="records")
# print(score_input)

# Test locally
# from src.code.mlcode.scoretft import init, run

# init(scoring_config_parsed)
# pred_result = run(data)
# print(pred_result.to_dict("records"))

from src.code.mlcode.scoredeepmc import init, run

init(scoring_config_parsed)
pred_result = run(data)
print(pred_result.to_dict("records"))

# import requests
# import json

# url = 'http://104.211.211.247/predict/'
# x = requests.post(url, json={'data':score_input})

# print(x.text)
