#Copyright (c) Microsoft. All rights reserved.
import datetime
import logging
import os
import json
import pandas as pd

import azure.functions as func
from modules.testStreamingData import streamingData
from utilities.azure import blobOperations
from utilities.dboperations import dboperations
import goliveappconfig

def main(mytimer: func.TimerRequest) -> None:

    # Get pred date from database
    # Read prediction date from database

    fileidentifier = goliveappconfig.iotFileIdentifier
    
    # Generate and upload blob
    date = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
    df, entity_df = streamingData.generateData()
    dt = date.strftime('%Y-%m-%d_%H%M%S')
    blob = f"{fileidentifier}_{dt}.csv"

    blobOperations.uploadDFToBlobStorage(df,goliveappconfig.sourceStreamingStorageAccount, goliveappconfig.sourceStreamingDataContainerName, blob,includeIndex=False)
    
    blob_entity = f"{goliveappconfig.entityFileIdentifier}_{dt}.csv"

    blobOperations.uploadDFToBlobStorage(entity_df,goliveappconfig.sourceStreamingStorageAccount, goliveappconfig.sourceStreamingDataContainerName, blob_entity,includeIndex=False)
