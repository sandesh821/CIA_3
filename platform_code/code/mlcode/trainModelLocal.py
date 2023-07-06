#Copyright (c) Microsoft. All rights reserved.
from HyperparameterTuning import optimize
import pandas as pd
import os
import yaml
import ast
import runpy
import sys

#===================Load configurations===================
try:
    with open('../config.yaml', 'r') as file:
        confg = yaml.safe_load(file)
except (IOError, ValueError, EOFError, FileNotFoundError) as ex:
    logging.error("Config file not found")
    logging.error(ex)
    raise ex
except Exception as YAMLFormatException:
    logging.error("Config file not found")
    logging.error(YAMLFormatException)
    raise YAMLFormatException


#=======================Parse configurations======================
connection_config = str(confg.get('SourceConfig',{})) 
preprocess_config =  str(confg.get('PreprocessConfig',{}))
train_config =  str(confg.get('TrainConfig',{}))
train_pipeline_config = str(confg.get('PipelineConfig',{}))
tp = str(confg.get('PipelineConfig',{}))
train_pipeline_config = ast.literal_eval(train_pipeline_config) 
SourceConfig = ast.literal_eval(connection_config) 
PreprocessConfig = ast.literal_eval(preprocess_config)  

# Read Experiment Configurations
experimentName = train_pipeline_config.get("experimentName","defaultTraining")
environmentNames = train_pipeline_config.get("environmentName")
cpuClusterNames = train_pipeline_config.get("cpuClusterName")
preprocessCluster = train_pipeline_config.get("preprocessCluster","defaultCluster")
preprocessEnvironmentName = train_pipeline_config.get("preprocessEnvironmentName","defaultEnvironment")
scriptSourceDir = train_pipeline_config.get("scriptSourceDir")
environmentYAMLFiles = train_pipeline_config.get("environmentYAMLFile")
entryPoints = train_pipeline_config.get("entryPoint")
dataFileNames = train_pipeline_config.get("dataFileName")
outputFolderName = train_pipeline_config.get("outputFolderName")
models = train_pipeline_config.get("models")

if __name__ == "__main__":

    modelCount = len(models)
    for i in range(modelCount):

        # Load model specific configurations
        modelName = models[i]
        entryPoint = entryPoints[i]
        dataFileName = dataFileNames[i]
        sys.argv = ['','--input', '../data/', "--output", outputFolderName,"--modelName",modelName,"--train_config",train_config,"--preprocess_config",preprocess_config ,"--train_pipeline_config",tp, "--dataFileName",dataFileName]
        runpy.run_path('./'+entryPoint)
    
