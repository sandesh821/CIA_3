#Copyright (c) Microsoft. All rights reserved.
from azureml.core import Workspace
from azureml.data import OutputFileDatasetConfig
from azureml.core.runconfig import RunConfiguration, HistoryConfiguration
from azureml.pipeline.steps import PythonScriptStep
from azureml.core import Dataset, Datastore
from azureml.core.compute import AmlCompute
from azureml.core import Environment
from azureml.core.conda_dependencies import CondaDependencies
from azureml.core import Experiment
from azureml.pipeline.core import Pipeline
from azureml.core.compute_target import ComputeTargetException
from azureml.core import ComputeTarget

import preprocess_step
import pandas as pd
import yaml
import ast
import logging
import os
import argparse
import requests
import json

from masterConfiguration import azureDetails
from dboperations.dboperations import executeStoredProcedure
from amloperations.amloperations import getAMLWorkspace

#from utilities.azure import devops
#from utilities import config
#===============Read configuration file name from arguments or use the default configuration==============
parser = argparse.ArgumentParser("split")
parser.add_argument("--configFile", type=str, help="Configuration File Name")
args, _ = parser.parse_known_args()
if args.configFile:
    configFilePath = args.configFile
else:
    configFilePath = 'config.yaml' #default config
logging.info("Running for config: ", configFilePath)

#===================Load configurations===================
try:
    with open(configFilePath, 'r') as file:
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
scoringpipeline_config = str(confg.get('ScoringPipelineConfig',{}))
scoring_config = str(confg.get('ScoringConfig',{}))

scoringpipeline_config = ast.literal_eval(scoringpipeline_config)
scoring_config_parsed = ast.literal_eval(scoring_config)

## Scoring pipeline Configurations
experimentName = scoringpipeline_config.get("experimentName","defaultScoringExpName")
experimentSetName = scoringpipeline_config.get("experimentSetName","defaultScoringSet")
experimenttag = scoringpipeline_config.get("experimentTag","defaultTag")
environmentName = scoringpipeline_config.get("environmentName","defaultEnvironment")
cpuClusterName = scoringpipeline_config.get("cpuClusterName","defaultcomputecluster")
scriptSourceDir = scoringpipeline_config.get("scriptSourceDir")
environmentYAMLFile = scoringpipeline_config.get("environmentYAMLFile")
entryPoint = scoringpipeline_config.get("entryPoint")
modelName = scoring_config_parsed.get("modelName")
modelPath = scoring_config_parsed.get("modelPath")
internalRunId = modelPath.split("/")[-2]
logging.info(internalRunId)

#===================1.0 Load workspace===================
ws = getAMLWorkspace()


#===================2.0 Create an experiment===================
experiment = Experiment(ws, experimentName)
logging.info('Experiment name: ' + experiment.name)

#===================3.0 Create environment===================
try:
    # Load existing environment if exists, else create one
    train_env = Environment.get(workspace=ws,name=environmentName)
except:
    train_env = Environment(environmentName)
    train_env.python.conda_dependencies = CondaDependencies(conda_dependencies_file_path=environmentYAMLFile)
    train_env.register(workspace=ws)

#===================4.0 Select a compute target===================
try:
    # Load existing compute if exists, else create one
    compute = AmlCompute(ws, cpuClusterName)
    logging.info('Found existing cluster, use it.')
except ComputeTargetException:
    compute_config = AmlCompute.provisioning_configuration(vm_size='Standard_DS12_v2',max_nodes=2)
    compute = ComputeTarget.create(ws, cpuClusterName, compute_config)
    compute.wait_for_completion(show_output=True)

#===================5.0 Create run configurations and define input dataset===================
# create a new runconfig object
history_config = HistoryConfiguration()
history_config.output_collection=False
history_config.snapshot_project=False

# create a new runconfig object
run_config = RunConfiguration()
run_config.environment = train_env
run_config.history = history_config


#-------

#================= Upload Configuration used in the run========
datastore = ws.get_default_datastore()
datastore.upload_files(files=[configFilePath],target_path=modelPath,overwrite=True,show_progress=True)
#-----

#===================6.0 Create Pipeline Step===================

score_step = PythonScriptStep(
        script_name=entryPoint,
        source_directory=scriptSourceDir,
        compute_target=compute,
        arguments=['--scoring_config', scoring_config],
        runconfig=run_config,
        allow_reuse=True
    )

#===================7.0 Build the pipeline===================
comparisonPipeline = Pipeline(workspace=ws, steps=score_step)

#===================8.0 Submit the pipeline to be run===================
pipeline_run = experiment.submit(comparisonPipeline)
pipeline_run.tag(modelName)
pipeline_run.tag(experimenttag)
pipeline_run.tag(internalRunId)
run_id = pipeline_run.get_details().get("runId")
 # Create log before starting job
try:
    executeStoredProcedure("usp_InsertRunTracking","@ExperimentSet=?,@Experiment = ?, @InternalRunID = ?, @AMLRunId = ?, @RunStatus = ?", (experimentSetName,experimenttag,internalRunId,run_id, "Batch Scoring Started"),"logs",0)
except Exception as ex:
    logging.error(ex)
    logging.info("Cancelling pipeline run")  
    pipeline_run.cancel() 
    raise ex

try:   
    pipeline_run.wait_for_completion(show_output=True, timeout_seconds=9223372036854775807, raise_on_error=True)
except Exception as ex:
    logging.error(ex)   
    raise ex
finally:
    logging.info("Pipeline complete!")
    # Save status and timestamp for any run of experiment 
    run_status = pipeline_run.get_status()
    logging.info(run_id)
    logging.info(run_status)
    try:
        if run_status == "Finished":
            # Get run type (workflow or retraining), if retraining deploy the retrained model else skip
            runDetails = executeStoredProcedure("usp_getExperimentRunSource","@ExperimentSet=?,@Experiment = ?", (experimentSetName,experimenttag),"golive",2)
            logging.info(runDetails)
            if runDetails is not None:
                runDetails = runDetails.to_dict("records")
                runDetails = runDetails[0]
                if runDetails["CreatedSource"] == "retraining":
                    experimentSetId = runDetails["ExperimentSetId"] 

                    # Update best model with soft delete to old value
                    modelDetails = executeStoredProcedure("usp_getModelDetails","@ExperimentSetID =?",(experimentSetId),"golive",1)
                    modelDetails = json.loads(modelDetails[0])
                    modelDetails["best_model"]["InternalRunId"] = internalRunId

                    logging.info(modelDetails)
                    executeStoredProcedure("usp_insertModelDetails","@ExperimentSetID =?,@ModelDetails=?",(experimentSetId, json.dumps(modelDetails)),"golive",0)

                    # Submit web request to deploy retrained model
                    # data = {
                    #     "experimentsetid":experimentSetId,
                    #     "experimentsetname" : experimentSetName,
                    #     "fileUpload" : "false",
                    #     "deploymentType" : "best"
                    # }
                    # devops.generateDevOpsRequest(config.GoLiveAppDeployemntBuildId,data)
                    # devops.generateDevOpsRequest(config.DeploymentManagerBuildId,data)

        executeStoredProcedure("usp_InsertRunTracking","@ExperimentSet=?,@Experiment = ?, @InternalRunID = ?, @AMLRunId = ?, @RunStatus = ?", (experimentSetName,experimenttag,internalRunId,run_id, "Batch Scoring "+ run_status),"logs",0)

    except Exception as ex:
        logging.error(ex)   
        raise ex

print("Processing complete!")