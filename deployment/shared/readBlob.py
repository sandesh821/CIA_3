#Copyright (c) Microsoft. All rights reserved.
import os
import pandas as pd 
import json
import logging
import datetime
from io import StringIO

from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential

def loadDataFromBlob(strgAccountName,container_name,blob_name):
    try:
        default_credential = DefaultAzureCredential()
        blob_service_client = BlobServiceClient(account_url="https://"+strgAccountName+".blob.core.windows.net", credential=default_credential)    
    except Exception as ex:
        logging.error(ex)
        print("Error in generating credentials")
    container_client = blob_service_client.get_container_client(container_name)
    downloaded_blob = container_client.download_blob(blob_name)
    df = pd.read_csv(StringIO(downloaded_blob.content_as_text()), parse_dates=True, index_col=0)
    return df

def saveDFToBlob(strgAccountName,container_name,df,blob_path):
    default_credential = DefaultAzureCredential()
    blob_service_client = BlobServiceClient(account_url="https://"+strgAccountName+".blob.core.windows.net", credential=default_credential)    
    container_client = blob_service_client.get_container_client(container_name)

    output = df.to_csv(encoding = "utf-8")
    blob_client = container_client.get_blob_client(blob_path)
    blob_client.upload_blob(output, overwrite=True)
# Test script
# print(loadDataFromBlob("streamingmasterdata","masterdata","hsexp1/experiment1/deepmc_score_input.csv"))