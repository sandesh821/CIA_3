#Copyright (c) Microsoft. All rights reserved.
from workflow.common.ResamplerMethods import ResamplerMethods
from utilities.azure import blobOperations
from utilities.dboperations import dboperations
from workflow.common import getdata
import goliveappconfig
import logging
import pandas as pd
import datetime
import json

def loadData(FileIdentifier,blob_list_names,foldername):

    all_df = []
    searchStr = f"{goliveappconfig.filePathPrefix}/{foldername}/"+FileIdentifier

    finalBlobList = []
    if len(blob_list_names) > 0:
        for blob in blob_list_names:
            if searchStr in blob: 
                _,df,_ = blobOperations.getBlobDf(goliveappconfig.sourceStorageAccount,goliveappconfig.sourceRawDataContainerName, blob)
                all_df.append(df)
                finalBlobList.append(blob)

        if len(finalBlobList) > 0:
            final_df = pd.concat(all_df)
            
            print(final_df)
            return final_df,finalBlobList
        else:
            return None, []

def appendData(date):
    
    dt = (pd.to_datetime(date)+ datetime.timedelta(days=-1)).strftime('%Y-%m-%d')

    # Get list of all blobs to be merged (prepare iot data file for that prediction)
    blob_list_names, _ = blobOperations.getBlobList(goliveappconfig.sourceRawDataContainerName, goliveappconfig.sourceStorageAccount)
    
    finalBlobList = []
    if len(blob_list_names) > 0:
        dfn_iot, iot_blobList = loadData(goliveappconfig.iotFileIdentifier,blob_list_names,"iot")
        dfn_entity, entity_blobList = loadData(goliveappconfig.entityFileIdentifier,blob_list_names,"entity")
        finalBlobList= iot_blobList+entity_blobList
        return dfn_iot,dfn_entity,finalBlobList
    
    else:
        logging.info("No files available in source data for date "+dt)
        return pd.DataFrame()
