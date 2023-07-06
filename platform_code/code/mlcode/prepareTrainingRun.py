#Copyright (c) Microsoft. All rights reserved.
from azureml.core import Run
import os
import datetime
import logging
from azureml.core.model import Model
import json
import inspect

from HyperparameterTuning import optimize
from ErrorAnalysis import executeMain

from dboperations.dboperations import executeStoredProcedure
from logUtils import get_AMLRunId, update_training_status, get_ChildAMLRunId
from logConfig import (
    PREPARE_HYPER_PARAMETER_TUNING,
    FINISHED_HYPER_PARAMETER_TUNING,
    STARTING_TRAINING_ERROR_ANALYSIS,
    ENDING_TRAINING_ERROR_ANALYSIS
)


def runTrain(args,masterParams,preprocess_config,modelClass):
    modelName = args.modelName
    outputPath = args.model_output
    model_input = args.model_input

    # If AMLRunId exists, execute stored procedure
    AMLRunId = get_AMLRunId(modelPath=outputPath)
    ChildAMLRunId = get_ChildAMLRunId(modelPath=outputPath)
    #=====================Define default configurations================
    masterParams["horizon"] = preprocess_config["lookahead"]
    masterParams["lookback"] = preprocess_config["lookback"]
    masterParams["freq"] = str(preprocess_config["frequency"])+preprocess_config["frequency_duration"]
    masterParams["frequency"] = preprocess_config["frequency"]
    masterParams["frequency_duration"] = preprocess_config["frequency_duration"]

    multiplicationFactorDict = {"H":1, "min" : (60), "S" : (60*60)}
    multiplicationFactor = multiplicationFactorDict.get(preprocess_config["frequency_duration"])
    masterParams["multiplicationFactor"] = multiplicationFactor
    
    trainParams=masterParams["parameters"]
    
    # ================Set up output directory and the results list=================
    if not os.path.isdir(outputPath):
        os.makedirs(outputPath)
    print("============Starting model training: ", modelName,"=============")

    # ===============Set the path of source file=====================
    masterParams["datasetPath"] = model_input
    masterParams["modelName"] = modelName
    masterParams["modelPath"] = outputPath+"/"
    masterParams["dataFileName"] = args.dataFileName
        
    #================Intialize training parameters======================
    trainingParameters = trainParams[modelName]
    
    # ===============Invoke Hyperparameter tuning ===============
    if (masterParams["isOptimizationEnabled"]):
        # If AMLRunId exists, execute stored procedure
        n_tuning_trials = masterParams["n_tuning_trials"]
        update_training_status(AMLRunId,PREPARE_HYPER_PARAMETER_TUNING,None,-1,n_tuning_trials,None,ChildAMLRunId,None)
        
        n_tuning_trials = masterParams["n_tuning_trials"]
        best_params = optimize(modelClass.objective,n_tuning_trials,model_input,masterParams)
        
        # If AMLRunId exists, execute stored procedure
        update_training_status(AMLRunId,FINISHED_HYPER_PARAMETER_TUNING,None,-1,n_tuning_trials,None,ChildAMLRunId,None)
        # ================Save the best parameters in the output folder==============
        json_object = json.dumps(best_params)
        with open(outputPath+'/'+modelName+"/params.json", "w") as outfile:
            outfile.write(json_object)

        #  ===============Update training parameters with optimized params ===============
        for key in best_params:
            if key in trainingParameters.keys():
                trainingParameters[key] = best_params[key]
            elif key in masterParams["forecast_params"].keys():
                masterParams["forecast_params"][key] = best_params[key]

    #================Update tuned parameters in the master parameters======================== 
    masterParams["parameters"] = trainingParameters

    #================================Invoke Model initialization, training and validation ====================
    model = invokeModelTrainingAndValidation(modelClass,masterParams,outputPath,modelName)

    # ===============Error Analysis======================
    if(masterParams["isErrorAnalysisEnabled"]):
        invokeErrorAnalysis(outputPath,modelName)
    
    return model

def invokeModelTrainingAndValidation(modelClass,masterParams,outputPath,modelName):
    #  ================================Model initialization and training ====================
    logging.info("Start: Model training")
    model = modelClass(masterParams)
    modelFilePath = model.trainModel()
    logging.info("End: Model training")
    
    #  ==========================================Model Validation=============================
    logging.info("Start: Model validation")
    if(masterParams["isValidationEnabled"]):
        logging.info("Start: Model validation")
        model.testModel()
        result_list = model.printResults()
        #  ===============Save the results  ===============  
        result_list.to_csv(outputPath+"/result_"+modelName+".csv", index=False)

        logging.info("End: Model validation")
    return model

def invokeErrorAnalysis(outputPath,modelName,masterParams):
    AMLRunId = get_AMLRunId(modelPath=outputPath)
    ChildAMLRunId = get_ChildAMLRunId(modelPath=outputPath)
    n_tuning_trials = masterParams["n_tuning_trials"]
    update_training_status(AMLRunId,STARTING_TRAINING_ERROR_ANALYSIS,None,-1,n_tuning_trials,None,ChildAMLRunId,None)
    logging.info("Start: Model error analysis")

    dataStorePath = outputPath+"/"+modelName 
    targetDSPath = outputPath+"/"+modelName 
    pred_col = 'Prediction'
    act_col = 'Actual'
    dat_col = masterParams["dateField"]+'Original'
    units = '(MW)'

    executeMain(dataStorePath,targetDSPath,modelName,pred_col,act_col,dat_col,units)
    n_tuning_trials = masterParams["n_tuning_trials"]
    update_training_status(AMLRunId,ENDING_TRAINING_ERROR_ANALYSIS,None,-1,n_tuning_trials,None,ChildAMLRunId,None)
    logging.info("End: Model error analysis")

def saveOutputs(current_run,outputPath,modelName):
    ws = current_run.experiment.workspace
    ds = ws.get_default_datastore() 
    ds.upload('./'+outputPath, target_path=outputPath, overwrite=True)

def createLog(current_run,outputPath,modelName):
    obj = outputPath.split("/")

    try:
        executeStoredProcedure("usp_InsertChildRunTracking","@Experiment = ?,@ModelName = ?, @InternalRunID = ?, @ChildAMLRunId = ?", (obj[2],modelName,obj[3],current_run.get_details().get("runId")),"logs",0)
    except Exception as ex:
        logging.error(ex)   
        raise ex