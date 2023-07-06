#Copyright (c) Microsoft. All rights reserved.
from azureml.core import Workspace
from azureml.core.runconfig import RunConfiguration, HistoryConfiguration
from azureml.pipeline.steps import PythonScriptStep
from azureml.core import Dataset, Datastore
from azureml.core.compute import AmlCompute
from azureml.core import Environment
from azureml.core.conda_dependencies import CondaDependencies
from azureml.core import Experiment
from azureml.pipeline.core import Pipeline
from azureml.pipeline.core import PipelineData, StepSequence
from azureml.core.compute_target import ComputeTargetException
from azureml.core import Run
from azureml.core import ComputeTarget
import json
import logging
import azureml._restclient.snapshots_client

def getAMLWorkspace():
    try:
        ws = Workspace.from_config()
    except Exception as ex:
        current_run = Run.get_context()
        ws = current_run.experiment.workspace
    return ws

def training_step(ws,model,environmentName,environmentYAMLFile,cpuClusterName,entryPoint,scriptSourceDir,outputFolderName,train_config,pred_idx,horizon):
    # Load model specific configurations
    modelName = model

    # Get model specific environment
    try:
        # Load existing environment if exists, else create one
        train_env = Environment.get(workspace=ws,name=environmentName)
    except:
        train_env = Environment(environmentName)
        train_env.python.conda_dependencies = CondaDependencies(conda_dependencies_file_path=environmentYAMLFile)
        train_env.register(workspace=ws)

    # Select compute cluster, if different for different model
    try:
        # Load existing compute if exists, else create one
        compute = AmlCompute(ws, cpuClusterName)
        logging.info('Found existing cluster, use it.')
    except ComputeTargetException:
        compute_config = AmlCompute.provisioning_configuration(vm_size='Standard_DS12_v2',max_nodes=2)
        compute = ComputeTarget.create(ws, cpuClusterName, compute_config)
        compute.wait_for_completion(show_output=True)
    
    history_config = HistoryConfiguration()
    history_config.output_collection=False
    history_config.snapshot_project=False

    # create a new runconfig object
    train_run_config = RunConfiguration()
    train_run_config.environment = train_env
    train_run_config.history = history_config

    modelPath = outputFolderName+"DeepMC/"
    # Create Step in pipeline for model training and validation
    train_step = PythonScriptStep(
        script_name=entryPoint,
        source_directory="./",
        arguments=["--modelName",modelName,"--params",train_config,"--modelPath",modelPath,"--pred_idx",pred_idx,"--horizon",horizon],
        compute_target=compute,
        runconfig=train_run_config,
        allow_reuse=True
    )
    return train_step

def buildPipelineStep(model,pipelineConfig,train_config,pred_idx,horizon):
    ws = getAMLWorkspace()
        
    # Read Experiment Configurations
    internalPipelineConfig = pipelineConfig.get("internalPipelineConfig")
    environmentName = internalPipelineConfig.get("environmentName")
    cpuClusterName = internalPipelineConfig.get("cpuClusterName")
    environmentYAMLFile = internalPipelineConfig.get("environmentYAMLFile")
    entryPoint = internalPipelineConfig.get("entryPoint")
    scriptSourceDir = pipelineConfig.get("scriptSourceDir")
    outputFolderName = pipelineConfig.get("outputFolderName")
    train_config = json.loads(train_config)
    train_config["experimentTag"] = pipelineConfig.get("experimentTag")
    train_config = json.dumps(train_config)
    
    train_step = training_step(ws,model,environmentName,environmentYAMLFile,cpuClusterName,entryPoint,scriptSourceDir,outputFolderName,train_config,pred_idx,horizon)

    return train_step


def buildPipeline(steps,pipelineConfig):
    azureml._restclient.snapshots_client.SNAPSHOT_MAX_SIZE_BYTES = 1000000000
    azureml._restclient.constants.SNAPSHOT_MAX_SIZE_BYTES = 1000000000

    #===================1.0 Load workspace========================
    ws = getAMLWorkspace()

    #===================2.0 Create an experiment===================
    # Read Experiment Configurations
    internalPipelineConfig = pipelineConfig.get("internalPipelineConfig")
    experimentName = internalPipelineConfig.get("experimentName","defaultTraining")
    experimentTag = pipelineConfig.get("experimentTag")

    experiment = Experiment(ws, experimentName)
    print('Experiment name: ' + experiment.name)

    #===================3.0 Create Pipeline===================   
    internalPipeline = Pipeline(workspace=ws, steps=steps)
    
    #===================4.0 Submit Pipeline===================
    pipeline_run = experiment.submit(internalPipeline)
    pipeline_run.tag(experimentTag)
    pipeline_run.tag(pipelineConfig.get("outputFolderName"))

    pipeline_run.wait_for_completion(show_output=True, timeout_seconds=pipelineConfig.get('timeout'), raise_on_error=True)


def downloadModels(modelPath,modelType):
    print("Downloading training models")
    #===================1.0 Load workspace========================
    ws = getAMLWorkspace()
    ds = ws.get_default_datastore()
    print(modelPath+modelType)
    modelFolder = ds.download(target_path="./", prefix=modelPath+modelType)

def uploadToDatastore(modelPath):
    print("Uploading ", modelPath)
    #===================1.0 Load workspace========================
    ws = getAMLWorkspace()
    ds = ws.get_default_datastore() 
      #  ===============Upload the folder to the workspace's default data store ===============
    ds.upload(modelPath, target_path=modelPath, overwrite=True)

def uploadToDatastoreWithTargetPath(modelPath,targetPath):
    print("Uploading ", modelPath)
    #===================1.0 Load workspace========================
    ws = getAMLWorkspace()
    ds = ws.get_default_datastore() 
      #  ===============Upload the folder to the workspace's default data store ===============
    ds.upload(modelPath, target_path=targetPath, overwrite=True)
    