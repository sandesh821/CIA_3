#Copyright (c) Microsoft. All rights reserved.
# Setting Path for Pre-Built Module Import Setup
import os
import sys 
utilities_path = os.path.abspath(os.path.join(os.getcwd(), '..', '..'))
sys.path.append(utilities_path) 
import logging
# Importing Utilites
from utilities import config
from utilities.azure import blobOperations
from utilities.dboperations import dboperations
from datetime import datetime as dt
from datetime import datetime, date, timedelta
import pandas as pd
def convertDateToStr(date):
    return dt.strftime(date, "%Y-%m-%d %H:%M:%S")
def convertStrToDate(strDate):
    return dt.strptime(strDate, "%Y-%m-%d %H:%M:%S")
# Reading Blob Data
def scheduleRetrainingExperiment(goliveappconfig):
    '''
    Function to handle the Retraining Module Process.
    1. Fetched Data from Blob.
    2. Updated the PreprocessedFile in Blob Storage with Specified Dates.
    3. Added data in the DB to re-schedule the experiment.
    Args:
        cfg::[dict]
            Config dictionary containing inputs for Retraining Module.
    Returns:
        None
    '''
    # Get Experiment Data from database
    logging.info("Extracting experiment data from database")
    params_list = '@ExperimentSetID = ?, @ExperimentTag = ?'
    input_params = (goliveappconfig.experimentSetId,goliveappconfig.experimentTag)
    experiment_data = dboperations.executeStoredProcedure(
        'usp_getScheduledExperimentNameForRetraining', params_list, 
        input_params, SchemaName='golive', isGetResult=2
    )
    print(experiment_data)
    # Identify the retraining date ranges
    # convert string to date object
    trainingDataRangeInDays = (convertStrToDate(experiment_data['TrainEnd'][0]) - convertStrToDate(experiment_data['TrainStart'][0])).days
    validationDataRangeInDays = (convertStrToDate(experiment_data['ValEnd'][0]) - convertStrToDate(experiment_data['ValStart'][0])).days
    testDataRangeInDays = (convertStrToDate(experiment_data['TestEnd'][0]) - convertStrToDate(experiment_data['TestStart'][0])).days
    print(trainingDataRangeInDays,validationDataRangeInDays,testDataRangeInDays)
    # Fetching Preprocessed Data File
    _, preprocessed_df, _ = blobOperations.getBlobDf(
        goliveappconfig.sourceStorageAccount, goliveappconfig.sourceMasterDataContainerName, 
        goliveappconfig.filePathPrefix+"/masterdata.csv"
    )
    preprocessed_df = preprocessed_df[:-goliveappconfig.forecastHorizon]
    print(preprocessed_df[-1:]["DateTime"].values[0])
    latestDate = pd.to_datetime(preprocessed_df[-1:]["DateTime"].values[0])
    experiment_data['TestEnd'][0] = latestDate
    experiment_data['TestStart'][0] = latestDate - timedelta(days = testDataRangeInDays)
    experiment_data['ValEnd'][0] = latestDate - timedelta(days = testDataRangeInDays, hours=1) 
    experiment_data['ValStart'][0] = latestDate - timedelta(days = (testDataRangeInDays+validationDataRangeInDays))
    experiment_data['TrainEnd'][0] = latestDate - timedelta(days = (testDataRangeInDays+validationDataRangeInDays), hours=1)
    if not (goliveappconfig.historyEnabled):
        experiment_data['TrainStart'][0] = latestDate - timedelta(days = (testDataRangeInDays+validationDataRangeInDays+trainingDataRangeInDays))
    else:
        experiment_data['TrainStart'][0] = pd.to_datetime(experiment_data['TrainStart'][0])
    preprocessed_df = preprocessed_df.set_index(pd.DatetimeIndex(preprocessed_df["DateTime"]))
    preprocessed_df = preprocessed_df.drop(columns=["DateTime"])
    print(preprocessed_df)
    # # Slicing Data on the as per given
    preprocessed_df_retraining = preprocessed_df[
        (preprocessed_df.index >= experiment_data['TrainStart'][0]) & 
        (preprocessed_df.index <= experiment_data['TestEnd'][0])
    ]
    # Upload Data to Blob
    blobOperations.uploadDFToBlobStorage(
        preprocessed_df_retraining, goliveappconfig.trainingSourceStorageAccount, goliveappconfig.trainingSourceContainerName, 
        f'workflow/{goliveappconfig.experimentSetName}/MergedFilesRetrain/PreprocessedFile.csv'
    )
    # Convert datetime values to str
    experiment_data['TrainStart'][0] = convertDateToStr(experiment_data['TrainStart'][0])
    experiment_data['TrainEnd'][0] = convertDateToStr(experiment_data['TrainEnd'][0])
    experiment_data['ValStart'][0] = convertDateToStr(experiment_data['ValStart'][0])
    experiment_data['ValEnd'][0] = convertDateToStr(experiment_data['ValEnd'][0])
    experiment_data['TestStart'][0] = convertDateToStr(experiment_data['TestStart'][0])
    experiment_data['TestEnd'][0] = convertDateToStr(experiment_data['TestEnd'][0])
    # Preparing DataFrame to insert experiment for retraining into DB
    no_input_required_columns = ['ID', 'CreatedBy', 'CreatedOn']
    experiment_data.drop(no_input_required_columns, axis=1, inplace=True)
    experiment_data['CreatedSource'][0] = 'retraining'
    experiment_data['Status'][0] = 0
    experiment_data["MergedFile"] = "MergedFilesRetrain/PreprocessedFile.csv"
    print(experiment_data.to_dict("records"))
    # Inserting Data to Table
    dboperations.insertDataFromDF(experiment_data, 'scheduledExperimentsList')
