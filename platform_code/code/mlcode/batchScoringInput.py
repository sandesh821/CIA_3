#Copyright (c) Microsoft. All rights reserved.
from azureml.core import Workspace
from azureml.core.runconfig import RunConfiguration
from azureml.pipeline.steps import PythonScriptStep
from azureml.core import Dataset, Datastore
from azureml.data.datapath import DataPath
import numpy as np
import pandas as pd
import logging
import os

def prepareDataset(ws,scoring_config_parsed):
    #=========================================================
    # Prepare scoring dataset
    datastore = ws.get_default_datastore()

    modelName = scoring_config_parsed.get("modelName")
    folderPath = scoring_config_parsed.get("modelPath")
    dataFolderName =  scoring_config_parsed.get("dataFolderName")
    dateField = scoring_config_parsed.get("dateField")
    errorAnalysisConfig = scoring_config_parsed.get("errorAnalysisConfig")
    train_end= errorAnalysisConfig.get("train_end")
    val_start= errorAnalysisConfig.get("val_start")
    val_end= errorAnalysisConfig.get("val_end")

    parameters = scoring_config_parsed.get("parameters")

    if (modelName == "DeepMC"):
        trunc = parameters[modelName]["trunc"]
        inputFileName = "deepmc_data.csv"
        outputFileName = "deepmc_score_input.csv"  
        lookahead = parameters[modelName]["horizon"]  
    else:
        inputFileName = "data.csv"
        outputFileName = "data_score_input.csv"
        lookahead = parameters[modelName]["forecast_horizon"]
    
    filePath = folderPath+modelName+"/sourcedata/"+inputFileName
    try:
        ds = Dataset.Tabular.from_delimited_files(path = [(datastore,filePath)],header='ALL_FILES_HAVE_SAME_HEADERS')
        if not os.path.isdir(dataFolderName):
            os.makedirs(dataFolderName,exist_ok=True)

        #===============Update index of dataset=========================
        sample = ds.to_pandas_dataframe()
        # Clean missing values
        sample = sample.set_index(pd.DatetimeIndex(sample[dateField]))
        print("Interpolated dataset count:", len(sample))
        
        # Filter the dataset
        if (modelName == "DeepMC"):
            startIndex = len(sample[sample[dateField+"Original"]>=val_start]) + trunc
            
            endIndex = len(sample[sample[dateField+"Original"]<=val_end])+lookahead
            score_input = sample[(len(sample) - startIndex): endIndex]
        elif (modelName == "TFT"):
            lookback = parameters[modelName]["lookback"]

            startIndex = len(sample[sample[dateField+"Original"]<val_start])-lookback
            score_input = sample[startIndex:]
            endIndex = len(score_input[score_input[dateField+"Original"]<val_end])+lookahead
            score_input = score_input[:endIndex]
        else:
            score_input = sample[sample[dateField+"Original"]>=val_start]
            score_input = score_input[score_input[dateField+"Original"]<=val_end]

        print("dataset count:", len(score_input))
        
        score_input = score_input.reset_index(drop=True)
        score_input.to_csv(dataFolderName+outputFileName)
        Dataset.File.upload_directory(src_dir=dataFolderName,
                target=DataPath(datastore, dataFolderName),
                pattern="*.csv", overwrite=True, show_progress=True
                )

        print("Dataset created and uploaded in blob storage")
    except Exception as ex:
        logging.error(ex)
        logging.info("Data load failed")
