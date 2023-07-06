#Copyright (c) Microsoft. All rights reserved.

from azureml.core import Environment, Datastore
from utilities.azure.keyvaultOperations import getAMLWorkspace 
from azureml.core import Experiment, run
from azureml.pipeline.core import PipelineRun

def getEnvironmentDetails(env):
    ws = getAMLWorkspace()
    details = Environment.get(ws,env).get_image_details(workspace=ws)
    # print(details["ingredients"]["condaSpecification"])
    return details["dockerImage"]["name"]

def getEnvironmentVersion(env):
    ws = getAMLWorkspace()
    details = Environment.get(ws,env)
    return details.version

def getAMLContainer():
    ws = getAMLWorkspace()
    ds = Datastore.get_default(ws)
    return ds.container_name

def getAMLPipelineLogs(pipelineRunId):
    ws = getAMLWorkspace()
    print(pipelineRunId)
    # Get log files
    r = run.Run.get(ws, pipelineRunId)
    details = r.get_details()
    return details["logFiles"]

def getExperimentTags(expName,pipelineRunId):
    ws = getAMLWorkspace()
    experiment = Experiment(ws, expName)
    pipeline_run = PipelineRun(experiment, pipelineRunId)
    tags = pipeline_run.get_tags()
    tagList = []
    for tag in tags:
        tagList.append(tag)
    return ','.join(tagList)