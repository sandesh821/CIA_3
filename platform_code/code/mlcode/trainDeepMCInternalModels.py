#Copyright (c) Microsoft. All rights reserved.
from azureml.core import Run
import pandas as pd
import numpy as np
import os
import bz2
import argparse
import datetime
import joblib
import logging
from azureml.core import Datastore
from azureml.core.model import Model
import yaml
import ast
import pickle
import logging
import json
import time
import gc
import shutil
import pathlib

from deepmc import modelsv3_transformer
from deepmc import modelsvb
from DeepMCPipeline import *
from HyperparameterTuning import optimizeInternalModels
from logUtils import get_AMLRunId, update_training_status, get_ChildAMLRunId
import pathlib
from logConfig import (
    PREPARE_HYPER_PARAMETER_TUNING,
    RUNNING_HYPER_PARAMETER_TUNING,
    TRAINING_HYPER_PARAMETER_TUNING,
    FINISHING_HYPER_PARAMETER_TUNING,
    FINISHED_HYPER_PARAMETER_TUNING,
)


# Parse input arguments
parser = argparse.ArgumentParser("split")
parser.add_argument("--modelName", type=str, required=True, help="Model Name")
parser.add_argument('--pred_idx', type=str, dest='pred_idx')
parser.add_argument('--params', type=str, dest='params')
parser.add_argument('--modelPath', type=str, dest='modelPath')
parser.add_argument('--horizon',type=str,dest='horizon')

args, _ = parser.parse_known_args()

current_run = None

def buildInternalModels(obj, params,path):
    model = modelsv3_transformer.moddeepmc_pred_model(obj["train_X"], obj["ty"], validation_data=obj["validation_data"], params = params)
    # Layer 2 model (Optimize batchsize and epoch)
    model, score = modelsvb.deepmc_fit_model(model, obj["train_X"], obj["ty"], validation_data=obj["validation_data"], params = params)    
    model.save(path)

    # Clean memory after prediction 
    del model
    gc.collect()

    return score

def objectiveInternal(trial,obj,path,n_trials,pred_idx,horizon):
    # Try custom loss function
    # Wavelets (replication functions) - For advanced hyperparameter tuning
    # TODO: Pick the wavelet generation function can be also part of hyperparameter tuning, based on the column for which we are tuning(which module based on future covariates)
    # Hyperparameters we want optimize
    optimize_params = {
                "epochs":trial.suggest_int('epochs', 10,50,step=10),
                "batch_size" : trial.suggest_categorical('batch_size', [32,64]),
                "learning_rate" : trial.suggest_loguniform('learning_rate', 1e-3, 1e-1),
                "droprate":trial.suggest_float('droprate', 0.1, 0.3,step=0.1),
                "activation" : trial.suggest_categorical('activation',['relu', 'sigmoid', 'softplus', 'softsign', 'tanh', 'selu','elu', 'exponential']),
                "loss" : trial.suggest_categorical('loss',['mse', 'mae', "msle"])
            }

    # retrieves the file path of the model being trained
    pathlib_path = pathlib.Path(path)
    InnerModelName = pathlib_path.stem
    modelPath= path.replace(InnerModelName, '')
    modelName = pathlib.Path(modelPath).stem
    modelPath = modelPath.replace(modelName, '')
    ChildAMLRunId = get_ChildAMLRunId(modelPath=modelPath)

    # retrieves the AML run ID associated with the model
    AMLRunId = get_AMLRunId(modelPath=modelPath)

    # calculate the total epoch completed
    total_epoch = optimize_params['epochs']

    
    # update the status of the trial, first to "running", then to "training" and finally to "finished".

    status = RUNNING_HYPER_PARAMETER_TUNING
    update_training_status(AMLRunId,status,total_epoch,pred_idx,n_trials,trial.number,ChildAMLRunId,horizon)

    status = TRAINING_HYPER_PARAMETER_TUNING
    update_training_status(AMLRunId,status,total_epoch,pred_idx,n_trials,trial.number,ChildAMLRunId,horizon)
    rmse = buildInternalModels(obj,optimize_params,path)

    status = FINISHING_HYPER_PARAMETER_TUNING
    update_training_status(AMLRunId,status,total_epoch,pred_idx,n_trials,trial.number,ChildAMLRunId,horizon)
    return rmse

def init():
    global current_run
    current_run = Run.get_context()

def run():
    logging.info("================Starting pipeline run=============")
    init()
    modelName = args.modelName
    pred_idx = int(args.pred_idx)
    params = json.loads(args.params)
    modelPath = args.modelPath
    isOptimizationEnabled = params["isOptimizationEnabled"]
    tuningtrials = params["tuningtrials"]
    experimentTag = params["experimentTag"]
    modelParams = params["params"]
    horizon = int(args.horizon)
    modelType = "DeepMC"
    
    print("========Starting training of model ",pred_idx,"========")

    # retrieves the AML run ID associated with the model
    print("modelPath", modelPath)
    AMLRunId = get_AMLRunId(modelPath=pathlib.Path(modelPath).parent.as_posix())
    ChildAMLRunId = get_ChildAMLRunId(modelPath=pathlib.Path(modelPath).parent.as_posix())

    # Download 
    downloadModels(modelPath,modelType)

    outputFolderPath = modelPath+modelType
    logging.info("Downloading Preprocess model")

    f = bz2.BZ2File(modelPath+"/"+modelType+"_train.pkl",'rb')
    train_X, train_y, test_X, test_y, train_scaler,output_scaler, t_train_X, t_train_y, t_test_X, t_test_y,std_val = pickle.load(f)
    f.close()

    ty = train_y[:,[pred_idx],:]
    validation_data=[test_X, test_y[:,[pred_idx],:]]
    obj = {
        "train_X": train_X,
        "ty" : ty,
        "validation_data" : validation_data
    }
    paramFilePath = outputFolderPath+modelName+"_params.json"

    train_Params = None
    # hyperparameter tune internal models
    if(isOptimizationEnabled):
        logging.info("===========Start: Hyperparameter tuning============")
        update_training_status(AMLRunId,PREPARE_HYPER_PARAMETER_TUNING,None,pred_idx,tuningtrials,None,ChildAMLRunId,horizon)
        best_params = optimizeInternalModels(objectiveInternal,tuningtrials,obj,modelPath+modelName,pred_idx,horizon)
        train_Params = best_params

        # Save model params to a file
        json_object = json.dumps(train_Params)
        with open(paramFilePath, "w") as outfile:
            outfile.write(json_object)
        update_training_status(AMLRunId,FINISHED_HYPER_PARAMETER_TUNING,None,pred_idx,tuningtrials,None,ChildAMLRunId,horizon)
        logging.info("===========End: Hyperparameter tuning============")
    else:
        try:
            print("Downloading Parameters")
            print("outputs/DeepMCParameters/"+experimentTag+"/DeepMC"+modelName+"_params.json")
            downloadModels("outputs/DeepMCParameters/",experimentTag)
            paramFilePath = "outputs/DeepMCParameters/"+experimentTag+"/DeepMC"+modelName+"_params.json"
            if os.path.exists(paramFilePath):
                print("Tuned parameters found for the model ",modelName)
                with open(paramFilePath, "r") as f:
                    modelParams = json.load(f)
                train_Params = modelParams
            else:
                print("Loading default params")
                train_Params = modelParams[pred_idx]
        except Exception as ex:
            logging.error("Output folder not found, using default parameters")
            train_Params = modelParams[pred_idx]
            raise ex

    print("Running pipeline for model: ",pred_idx)
    score = buildInternalModels(obj,train_Params,modelPath+modelName)
    
    print("Training completed for model: ",pred_idx)
    print("Score for model",pred_idx,": ", score)

    uploadToDatastore(modelPath)
    
    shutil.rmtree("outputs")
    gc.collect()
    return score

run()