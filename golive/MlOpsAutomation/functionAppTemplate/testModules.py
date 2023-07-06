#Copyright (c) Microsoft. All rights reserved.
from modules.apiManager import Solcast
from modules.appendStreamingData import appendStreamingData
from modules.dataCleaning import transformations
from modules.testStreamingData import streamingData
import goliveappconfig
import requests
import pandas as pd
import json
import datetime
from utilities.azure import blobOperations
# Importing additional utilities
from modules.driftValidation import dataDriftValidation, targetDriftValidation

def testResampler():
    resampledDataDF = appendStreamingData.appendData("2023-04-19 00:00:00")
    print(resampledDataDF)

def customizeSolcastAPIData(df: pd.DataFrame,dt):
    # TODO: To be updated as per the 
    df["windGust"] = df["windSpeed"]
    updated_df = df.rename(columns={"period_end": "DateTime", "wind_speed_10m": "windSpeed"})
    updated_df["DateTime"] = pd.to_datetime(updated_df["DateTime"],utc=True).astype('datetime64[ns]').dt.tz_localize(None).dt.strftime('%Y-%m-%d %H:%M:%S')
    updated_df["DateTime2"] = pd.to_datetime(updated_df["DateTime"],utc=False)
    updated_df["AvailableTime"] = (dt + datetime.timedelta(days=-1)).strftime('%Y-%m-%d')+" 00:00:00"

    #TODO: limit the data as per forecast horizon
    blobOperations.uploadDFToBlobStorage(updated_df,goliveappconfig.sourceStorageAccount, goliveappconfig.sourceCleanedDataContainerName,"darksky.csv")
            
    return updated_df

import os
def testAPIManager():
    date = pd.to_datetime("2023-04-18 00:00:00")
    cfg = {'latitude': '37.839333'
           , 'longitude': '-84.27'
           , 'output_parameters': 'cloud_opacity,ghi'
           , 'period': 'PT60M', 'format': 'csv'
           , 'start_date': '2023-05-13T00:00:00'
           , 'end_date': '2023-05-14T00:00:00'
           , 'time_zone': 'utc'}
    # solcast = Solcast.Solcast(cfg)
    # solcastData = solcast.getData()
    print(os.getcwd())
    solcastData = pd.read_csv("Users/asthaagarwal/DevOps/ForecastingPlatform/golive/eventManagerFunctionApp/darksky_2023-04-18_000000.csv")
    print(solcastData)
    print(customizeSolcastAPIData(solcastData,date))

def testDataCleaning():
    fileConfigurations = {'iot': 'solarewbrown/experiment8/20230508091610/intermediateMerge/iot_2023-05-13_000000.csv', 'power': 'solarewbrown/experiment8/20230508091610/intermediateMerge/power_2023-05-13_000000.csv', 'solcast': 'solarewbrown/experiment8/20230508091610/api/solcast_2023-05-13_000000.csv'}
    transformations.runCleaning(56,fileConfigurations)

def testFunc():
    # # Check if Merge and Resampling completed for the prediction
    # If yes, trigger data validation
    # # Set up the endpoint URL for your Azure Function
    preddate = "2023-04-19_000000"
    endpoint_url = f"https://eventmanagerfunctionapp.azurewebsites.net/api/preprocessdata/{preddate}?code=RB43PzInwJV1vlky-SlwB2jmrvedVv-SlpbVboK-eakiAzFumBTulw=="

    # # Make the request to the endpoint URL
    response = requests.get(endpoint_url)
    # # Print the response from the function
    print(response)
    print(response.text)
    # for key , value in goliveappconfig.api
    #     print(key,value)

def testDataDrift():
    # Checking for DataDrift
    cfg = {
            'storage_acc_name': goliveappconfig.sourceStorageAccount,
            'container_name': goliveappconfig.sourceCleanedDataContainerName,
            'input_file_name': "solarewbrown/experiment8/20230508091610/PreprocessedFiles/data_2023-05-12_000000.csv",
            'source_storage_acc_name': goliveappconfig.sourceStorageAccount,
            'source_container_name': goliveappconfig.sourceMasterDataContainerName,
            'training_file_name': "solarewbrown/experiment8/20230508091610/masterdata.csv",
            'num_col_threshold' : goliveappconfig.num_col_threshold,
            'drift_share': goliveappconfig.drift_share,
            'targetDriftColList': goliveappconfig.targetDriftColList,
            "pastCovariates": goliveappconfig.pastCovariates,
            "futureCovariates": goliveappconfig.futureCovariates,
            "lookback" : goliveappconfig.lookback,
            "lookahead" : goliveappconfig.forecastHorizon
    }
    
    dataDrift = dataDriftValidation.DataDrift(config = cfg)
    try:
        drifts, dataset_drift = dataDrift.get_df_drifts()
    except Exception as e:
        print("evidently fails to install properly")
        raise(e)

    cfg["training_file_name"] = goliveappconfig.filePathPrefix+"/batchscoring.csv"
    cfg["input_file_name"] = goliveappconfig.filePathPrefix+"/predictions__2023-05-10_000000.csv"
    cfg["container_name"] = goliveappconfig.predictionContainerName
    tgtDrift= targetDriftValidation.TargetDrift(config = cfg)
    # print(tgtDrift.features_historical_drift_frame)
    # print(tgtDrift)

def testStreaming():
    a, b = streamingData.generateData()
    print(a)
    print(b)

from modules.dataMerge import dataMerge
def testMerge():
    path = "solarewbrown/experiment2/20230504103545/PreprocessedFiles/data_2023-05-05_000000.csv"
    # Merge the data with the master data
    _, mergedData, _ = blobOperations.getBlobDf(goliveappconfig.sourceStorageAccount,goliveappconfig.sourceCleanedDataContainerName,path)
    dataMerge.mergeWithMaster(mergedData,goliveappconfig)

from modules.retraining import retraining
def testRetraining():
    retraining.scheduleRetrainingExperiment(goliveappconfig)

# testAPIManager()
# testDataCleaning()
# testResampler()
# testFunc()
# testStreaming()
# testMerge()
# testDataDrift()
testRetraining()