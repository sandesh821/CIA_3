#Copyright (c) Microsoft. All rights reserved.
# from DartsTCN import DartsTCN
# from DartsNBeats import DartsNBeats
# from DartsTFT import DartsTFT
from DeepMC import DeepMC

from HyperparameterTuning import optimize
import pandas as pd
import os
# GLOBAL PARAMETERS
n_tuning_trials = 1

windParams ={
        "datasetPath":"",
        "modelPath":"",
        "blocks":24,
        "freq":"60min",
        "requiredColumns": ['WindSpeed'],
        "targetColumn": "Power",
        "futureCovariates": ["TheoriticalPower"],
        "dateField": "DateTime",
        "train_end": '2018-12-20 23:00:00',
        "val_start": '2018-12-24 00:00:00',
        "val_end": '2018-12-24 6:00:00',
        #Slicing hyperparameters
        "horizon":6, #12 for darts
        "lookback":24,
        #architecture and training hyperparameters 
        "parameters" : {},
        #----------------------------------------
        #Prediction and model evaluation hyperparameters
        "forecast_params": {"n":6,"forecast_horizon":6,"stride":24,"verbose":False,"last_points_only":False ,"startDate":'2018-12-25 23:00:00'},
        "isTrain":True
    }

#TRAINING PARAMETERS
trainParams={
    "DartsTCN":{"n_epochs": 1, "dropout":0.2,"dilation_base":2,"weight_norm":True,"hidden_size":2,"lstm_layers":True,"kernel_size":5,"num_filters":3,"random_state":0, "verbose":True},
    "DartsTFT": {"n_epochs": 1, "dropout":0.12,"num_attention_heads":4,"hidden_size":19,"lstm_layers":1,"batch_size":32,"add_relative_index":False,"random_state":0, "verbose":True},
    "DartsNBeats":{"num_stacks":10,"num_blocks":1,"num_layers":4,"layer_widths":512,"n_epochs": 1,"batch_size":64,"nr_epochs_val_period":1,"verbose":False},
    "DeepMC":{"Blockno":"block2","epochs":1,"trunc":512}
}

enableOptimization = False

if __name__ == "__main__":
    models = ["DeepTFT"]#,"DartsTCN","DartsNBeats"
    resultSet = []
    modelFilePaths = []
    for modelName in models:
        print("============Starting model training: ", modelName,"=============")
        
        
        # Set the path of source file
        path = os.getcwd()
        directory = os.path.dirname(path)
       
        windParams["datasetPath"] = directory
        windParams["modelName"] = modelName
        windParams["modelPath"] = directory+"/outputs/"
        print(windParams["modelPath"])
        trainingParameters = trainParams[modelName]
        # Hyper parameter tuning
        if enableOptimization:
            best_params = optimize(globals()[modelName].objective,n_tuning_trials,directory,windParams)

            # Update training parameters with optimized params
            for key in best_params:
                if key in trainingParameters.keys():
                    trainingParameters[key] = best_params[key]
                elif key in windParams["forecast_params"].keys():
                    windParams["forecast_params"][key] = best_params[key]

        windParams["parameters"] = trainingParameters
        
        # Start model training and test
        model = globals()[modelName](windParams)

        modelFilePath = model.trainModel()
        modelFilePaths.append(modelFilePath)
        model.testModel()
        resultSet.append(model.printResults())
        # Dockerize the models
    
    result_df = pd.concat(resultSet)
    result_df.to_csv("modelResults.csv")
    print(result_df.to_markdown())
