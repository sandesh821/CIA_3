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
from azureml.core import ComputeTarget
import azureml._restclient.snapshots_client
azureml._restclient.snapshots_client.SNAPSHOT_MAX_SIZE_BYTES = 1000000000

import pandas as pd
import yaml
import ast
import logging
import time
import os
import argparse
import gitinfo
import json
import preprocess_step as preprocess_step
import training_step as training_step
import validateConfig as validateConfig
from dboperations.dboperations import executeStoredProcedure
from amloperations.amloperations import getAMLWorkspace

def invokeTrainingPipeline(configFilePath):
    logging.info(configFilePath)
    logging.info("Initializing Pipeline configurations")
    #===================Load configurations===================
    try:
        logging.info("Loading config file" + configFilePath)
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
    connection_config = str(confg.get('SourceConfig',{})) 
    preprocess_config =  str(confg.get('PreprocessConfig',{}))   
    train_config =  str(confg.get('TrainConfig',{}))
    train_pipeline_config = str(confg.get('PipelineConfig',{}))
    train_pipeline_config_src = train_pipeline_config
    train_pipeline_config = ast.literal_eval(train_pipeline_config) 
    SourceConfig = ast.literal_eval(connection_config) 
    PreprocessConfig = ast.literal_eval(preprocess_config)  
    train_config_parsed = ast.literal_eval(train_config) 
    # Read Experiment Configurations
    experimentName = train_pipeline_config.get("experimentName","defaultTraining")
    experimentTag = train_pipeline_config.get("experimentTag","experiment")
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
    localPath = outputFolderName
    run_ts = time.strftime("%Y%m%d%H%M%S")
    outputFolderName = outputFolderName+"/"+experimentName +"/"+experimentTag+"/"+ run_ts
    basePath = os.getcwd()+"/code/"
    #===================1.0 Load workspace===================
    ws = getAMLWorkspace()
    # Datastore
    datastore = ws.get_default_datastore()
    #================= Save and upload DevOps JSON================
    try:
        logging.info("Saving code version details")
        # with open('codeversiondetails.json', 'w') as f:
        #     json.dump(gitinfo.get_git_info(), f)
        print(os.getcwd()+"/codeversiondetails.json")
        datastore.upload_files(files = [basePath+"codeversiondetails.json"],
                                target_path = outputFolderName,
                                overwrite = True,
                                show_progress = True)
    except Exception as ex:
        logging.error(ex)
    #================= Upload Configuration used in the run========
    datastore.upload_files(files = [configFilePath],
                            target_path = outputFolderName,
                            overwrite = True,
                            show_progress = True)
    #===================2.0 Create an experiment===================
    experiment = Experiment(ws, experimentName)
    logging.info('Experiment name: ' + experiment.name)
    #===================3.0 Create environment===================
    logging.info("Setting AML environment")
    try:
        # Load existing environment if exists, else create one
        pre_env = Environment.get(workspace=ws,name=preprocessEnvironmentName)
    except:
        pre_env = Environment(preprocessEnvironmentName)
        pre_env.python.conda_dependencies = CondaDependencies(conda_dependencies_file_path=basePath+"environment.yml")
        pre_env.register(workspace=ws)
    #===================4.0 Select a compute target for preprocessing===================
    logging.info("Checking compute cluster")
    try:
        # Load existing compute if exists, else create one
        preprocesscompute = AmlCompute(ws, preprocessCluster)
        logging.info('Found existing cluster, use it.')
    except ComputeTargetException:
        compute_config = AmlCompute.provisioning_configuration(vm_size='Standard_DS12_v2',max_nodes=2)
        preprocesscompute = ComputeTarget.create(ws, preprocessCluster, compute_config)
        preprocesscompute.wait_for_completion(show_output=True)
    #===================5.0 Create run configurations and define input dataset===================
    # create a new runconfig object
    run_config = RunConfiguration()
    run_config.environment = pre_env
    resultSet = []
    #===================6.0 Create Pipeline Step===================
    # =======================6.1 Preprocessing ========================
    splitfiles_ds = PipelineData(PreprocessConfig.get('output_location'),datastore=datastore)
    preprocess_directory = SourceConfig.get('scripts_directory')
    PreprocessStep = preprocess_step.data_preprocess_step(run_config,preprocess_directory,splitfiles_ds,preprocesscompute,preprocess_config,connection_config)
    # =======================6.2 Model training========================
    logging.info("Creating steps for training multiple models")
    try:
        # Prepare input zipped list for all lists
        inputs = validateConfig.zip_equal(models,environmentNames,environmentYAMLFiles,cpuClusterNames,entryPoints,dataFileNames)
        compare_models = training_step.training_steps(ws,inputs,scriptSourceDir,outputFolderName,splitfiles_ds,train_config,preprocess_config,train_pipeline_config_src,basePath)
        #===================7.0 Build the pipeline===================
        all_steps = StepSequence(steps=[PreprocessStep,compare_models])#
        comparisonPipeline = Pipeline(workspace=ws, steps=all_steps)
        #===================8.0 Submit the pipeline to be run===================  
        pipeline_run = experiment.submit(comparisonPipeline,continue_on_step_failure=True)
        pipeline_run.tag(experimentTag)
        pipeline_run.tag(str(models[0]))
        pipeline_run.tag(run_ts)
        run_id = pipeline_run.get_details().get("runId")
        # Create log before starting job
        try:
            executeStoredProcedure("usp_InsertRunTracking","@ExperimentSet=?,@Experiment = ?, @InternalRunID = ?, @AMLRunId = ?, @RunStatus = ?", (experimentName,experimentTag,run_ts,run_id, "Started"),"logs",0)
        except Exception as ex:
            logging.error(ex)
            logging.info("Cancelling pipeline run")  
            pipeline_run.cancel() 
            raise ex
        try:   
            pipeline_run.wait_for_completion(show_output=True, timeout_seconds=train_pipeline_config.get('timeout'), raise_on_error=True)
        except Exception as ex:
            logging.error(ex)   
            raise ex
        finally:
            # Save status and timestamp for any run of experiment 
            run_status = pipeline_run.get_status()
            logging.info(run_id)
            logging.info(run_status)
            try:
                executeStoredProcedure("usp_InsertRunTracking","@ExperimentSet=?,@Experiment = ?, @InternalRunID = ?, @AMLRunId = ?, @RunStatus = ?", (experimentName,experimentTag,run_ts,run_id, run_status),"logs",0)
            except Exception as ex:
                logging.error(ex)   
                # raise ex
        
        #===================9.0 Generate the final result file===================
        isValidationEnabled = train_config_parsed.get("isValidationEnabled")
        if(isValidationEnabled):
            #Create file list
            logging.info("Collating results")
            datasets = []
            for modelName in models:
                datasets.append(Dataset.Tabular.from_delimited_files(path = [(datastore,'/'+outputFolderName+'/result_'+modelName+'.csv')],header='ALL_FILES_HAVE_SAME_HEADERS'))
            # Load results from each pipeline, merge them and upload the final result file
            result = []
            for dataset in datasets:
                result.append(dataset.to_pandas_dataframe())
            results = pd.concat(result)
            if not os.path.isdir(localPath):
                os.makedirs(localPath,exist_ok=True)
            localPath = localPath+"/results.csv"
            results.to_csv(localPath)
            logging.info("Output folder upload starting")
            # Upload output files
            datastore.upload_files(files = [localPath],
                                target_path = outputFolderName,
                                overwrite = True,
                                show_progress = True)
        logging.info("Processing complete!")
    except ValueError as ValueError:
        logging.error("Input lists are of different lengths")
        logging.error("Processing aborted!")
        logging.error(ValueError)

#===============Read configuration file name from arguments or use the default configuration==============
parser = argparse.ArgumentParser("split")
parser.add_argument("--configFile", type=str, help="Configuration File Name")
args, _ = parser.parse_known_args()
if args.configFile:
    configFilePath = args.configFile
else:
    configFilePath = 'configyaml_generator/config.yaml' #default config

invokeTrainingPipeline(configFilePath)