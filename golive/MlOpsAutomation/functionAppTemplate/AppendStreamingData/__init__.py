#Copyright (c) Microsoft. All rights reserved.
import datetime
import logging
import os
import azure.functions as func
from modules.appendStreamingData import appendStreamingData
from utilities.azure import blobOperations
from utilities.dboperations import dboperations
import goliveappconfig
import pandas as pd

def main(mytimer: func.TimerRequest) -> None:

    # Read prediction date from database
    df_dt = dboperations.executeStoredProcedure(goliveappconfig.GET_PREDICTION_SCHEDULE ,"@ExperimentSetID =?",(goliveappconfig.experimentSetId),goliveappconfig.goLiveSchema,1)
    date = df_dt[0]
    logging.info(date)

    # # Check if Merge and Resampling completed for the prediction
    predictionFlowStatus = dboperations.executeStoredProcedure(goliveappconfig.GET_PREDICTION_SCHEDULE_STATUS ,"@ExperimentSetID =?",(goliveappconfig.experimentSetId),goliveappconfig.goLiveSchema,2)
    
    if (predictionFlowStatus["MergedResampling"].values[0] is not None and int(predictionFlowStatus["MergedResampling"].values[0]) == 1):
        logging.info("IoT data merge for latest prediction schedule already completed")
    else:
        dfn_iot,dfn_entity,finalBlobList = appendStreamingData.appendData(date)

        for blob in finalBlobList:
            # Move file to processed folder
            blobOperations.moveBlobFromToFolder(goliveappconfig.sourceStorageAccount,goliveappconfig.sourceStorageAccount,goliveappconfig.sourceRawDataContainerName,goliveappconfig.sourceProcessedDataContainerName,blob,blob)

        # Update status in db
        dboperations.executeStoredProcedure(goliveappconfig.UPDATE_PREDICTION_SCHEDULE ,"@ExperimentSetID =?,@PredictionDate=?,@MergeResampling=?",(goliveappconfig.experimentSetId,date,1),goliveappconfig.goLiveSchema,0)

        logging.info(dfn_iot)
        dt = pd.to_datetime(date).strftime('%Y-%m-%d_%H%M%S')
        blob = f"{goliveappconfig.filePathPrefix}/intermediateMerge/{goliveappconfig.iotFileIdentifier}_{dt}.csv"
        blobOperations.uploadDFToBlobStorage(dfn_iot, goliveappconfig.sourceStorageAccount,goliveappconfig.sourceRawDataContainerName, blob,includeIndex=False)

        logging.info(dfn_entity)
        blob = f"{goliveappconfig.filePathPrefix}/intermediateMerge/{goliveappconfig.entityFileIdentifier}_{dt}.csv"
        blobOperations.uploadDFToBlobStorage(dfn_entity, goliveappconfig.sourceStorageAccount,goliveappconfig.sourceRawDataContainerName, blob,includeIndex=False)