#Copyright (c) Microsoft. All rights reserved.
from azure.storage.blob import BlobServiceClient
from azure.identity import ManagedIdentityCredential
import logging
import os
import sys

from shared.config import storage_account,container_name

def move_file( source, target_folder):
    
    #Fetch the Managed Identity Credentials
    creds = ManagedIdentityCredential()

    #create blob service client
    blob_service_client = BlobServiceClient(account_url= (f"https://{storage_account}.blob.core.windows.net/") , credential=creds)   

    source_blob = (f"https://{storage_account}.blob.core.windows.net/{source}")
    source_file_path = source[source.index('/')+1:]
    file_name = source_file_path[source_file_path.index('/')+1:]
    target_file_path = f"{target_folder}/{file_name}"

    # Copy the blob from source to destination folder
    copied_blob = blob_service_client.get_blob_client(container_name, target_file_path)
    copied_blob.start_copy_from_url(source_blob)

    # Delete the blob from source folder
    remove_blob = blob_service_client.get_blob_client(container_name, source_file_path)
    remove_blob.delete_blob()

#Test script
if __name__ == "__main__":
    source="pi-data/raw/2021/RGTEC_A_Compressor/RGTSUDX-RGTECACOMPRESSOR_ADLS2_20211209192501.json"
    target_folder="baddata"
    log = move_file(source,target_folder)
    print(log)