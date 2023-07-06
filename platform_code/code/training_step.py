#Copyright (c) Microsoft. All rights reserved.
import os
from azureml.pipeline.steps import PythonScriptStep
from azureml.core.runconfig import RunConfiguration, HistoryConfiguration
from azureml.pipeline.core import PipelineData
from azureml.pipeline.core import PipelineParameter
from azureml.core.compute import AmlCompute
from azureml.core import Environment
from azureml.core.conda_dependencies import CondaDependencies
from azureml.core import Experiment
from azureml.core import ComputeTarget
from azureml.core.compute_target import ComputeTargetException
import logging

def training_steps(ws,inputs,scriptSourceDir,outputFolderName,splitfiles_ds,train_config,preprocess_config,train_pipeline_config,basePath):
    compare_models = []
    modelCount = len(inputs)

    for i in range(modelCount):
        # Load model specific configurations
        modelName = inputs[i][0]
        environmentName = inputs[i][1]
        environmentYAMLFile = inputs[i][2]
        cpuClusterName = inputs[i][3]
        entryPoint = inputs[i][4]
        dataFileName = inputs[i][5]

        # Get model specific environment
        try:
            # Load existing environment if exists, else create one
            train_env = Environment.get(workspace=ws,name=environmentName)
        except:
            train_env = Environment(environmentName)
            train_env.python.conda_dependencies = CondaDependencies(conda_dependencies_file_path=basePath+environmentYAMLFile)
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
        
        # create a new runconfig object
        history_config = HistoryConfiguration()
        history_config.output_collection=False
        history_config.snapshot_project=False

        train_run_config = RunConfiguration()
        train_run_config.environment = train_env
        train_run_config.history = history_config

        # select training script for model

        # Create Step in pipeline for model training and validation
        train_step = PythonScriptStep(
            script_name=entryPoint,
            source_directory=scriptSourceDir,
            inputs = [splitfiles_ds],
            arguments=['--input', splitfiles_ds, "--output", outputFolderName,"--modelName",modelName,"--train_config",train_config,"--preprocess_config",preprocess_config ,"--train_pipeline_config",train_pipeline_config, "--dataFileName",dataFileName],
            compute_target=compute,
            runconfig=train_run_config,
            allow_reuse=True
        )
        compare_models.append(train_step)
    return compare_models