#Copyright (c) Microsoft. All rights reserved.

from datetime import datetime, timedelta
from azure.storage.blob import generate_blob_sas, BlobSasPermissions
import utilities.config as config
from utilities.azure import keyvaultOperations, azuremlOperations
import os
from io import StringIO, BytesIO
import pandas as pd
from azure.identity import ClientSecretCredential
from azure.mgmt.storage import StorageManagementClient
from azure.storage.blob import BlobServiceClient
import logging
account_name = config.STORAGEACCOUNTNAME
container_name = config.CONTAINERNAME

# Get account key from key vault
def getSecrets(key):
    try:
        global account_key
        (account_key,) = keyvaultOperations.getSecrets([key])
    except Exception as ex:
        print(ex)
        print("Error in reading blob secrets!")
    return account_key

# Generate Blob SAS for specified storage account
def __getBlobSas__(account_name,account_key, container_name, blob_name):
    sas_blob = generate_blob_sas(account_name=account_name, 
                                container_name=container_name,
                                blob_name=blob_name,
                                account_key=account_key,
                                permission=BlobSasPermissions(read=True),
                                expiry=datetime.utcnow() + timedelta(hours=1))
    return sas_blob

# Get Account Key
def __getAccountKey__(account_name):
    key = account_name+"key"
    # globals [key]
    try:
        print("Use existing account key")
        return globals()[key]
    except Exception as ex:
        print("Get account key from vault")
        globals()[key] = getSecrets(key)
        return eval(key) #globals[key]

# Prepare Storage account url
def __getStorageAccountURL__(account_name):
    return f'https://{account_name}.blob.core.windows.net'

def __getContainerClient__(strgAccountName,container_name):
    account_key = __getAccountKey__(strgAccountName)
    blob_service_client = BlobServiceClient(account_url=__getStorageAccountURL__(strgAccountName), credential=account_key)    
    container_client = blob_service_client.get_container_client(container_name)
    return container_client

# Generate blob url for the blob in the specified container
def getBlobURL(container_name, blobPath, strgAccountName = None):
    if strgAccountName is None:
        strgAccountName = account_name
    account_key = __getAccountKey__(strgAccountName)

    blob = __getBlobSas__(strgAccountName,account_key, container_name, blobPath)
    url = __getStorageAccountURL__(strgAccountName)+'/'+container_name+'/'+blobPath+'?'+blob
    return url

def getBlobDf(strgAccountName,container_name,blob_name):
    if strgAccountName == "default":
        strgAccountName = account_name 
    container_client = __getContainerClient__(strgAccountName,container_name)
    downloaded_blob = container_client.download_blob(blob_name)
    df = pd.read_csv(StringIO(downloaded_blob.content_as_text()))
    cols = df.columns
    return df.head(5),df,cols

def getBlobDfFromAMLStorageContainer(blob_name):
    return getBlobDf(account_name,azuremlOperations.getAMLContainer(),blob_name)

def __getStorageClient__(subscription_id):
    global storage_client
    try:
        print("Load existing storage client")
        return storage_client
    except Exception as ex:
        print("Create storage client")
        
        tenant_id = getSecrets('tenantid')
        client_id=  getSecrets('clientid')
        client_secret =  getSecrets('clientsecret') 
        credential = ClientSecretCredential(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret
        )
        storage_client = StorageManagementClient(credential, subscription_id)
        return storage_client

def getStorageAccountList():
    storage_accounts_ls = []
    for idx, subscription_id in enumerate(config.SUBSCRIPTIONID):
        storage_client = __getStorageClient__(subscription_id)
        resourceGroup = config.RESOURCEGROUP[idx]

        storage_accounts_obj = storage_client.storage_accounts.list_by_resource_group(resource_group_name=resourceGroup)
        storage_accounts = []
        for i in storage_accounts_obj:
            storage_accounts.append(i.name)
        storage_accounts_ls = storage_accounts_ls + storage_accounts

    return storage_accounts_ls

def getContainerList(storage_account,containers_ls = None):
    global blob_service_client
    account_key =  __getAccountKey__(storage_account)
    blob_service_client = BlobServiceClient(account_url=__getStorageAccountURL__(storage_account), credential=account_key)                                                                                      
    containers_obj = blob_service_client.list_containers()
    containers = []
    for i in containers_obj:
        containers.append(i.name)
    # If filter for list of containers is provided
    if containers_ls is not None:
        containers = list(set(containers).intersection(set(containers_ls)))
    return containers

def getBlobList(container,storage_account = account_name):
    blob_list = []
    if "blob_service_client" not in locals() and "blob_service_client" not in globals():
        container_client = __getContainerClient__(storage_account,container)
    else:
        container_client = blob_service_client.get_container_client(container)

    blobList = container_client.list_blobs()
    for blb in blobList:
        blob_list.append(blb.name)
    return blob_list, blobList

def uploadBlob(blob_name):
    container_client = __getContainerClient__(account_name,container_name)
    with open(blob_name, 'rb') as data:
      container_client.upload_blob( name = blob_name ,data=data,overwrite =True)

def parseBlobContent(downloaded_blob,targetPath,blob_name,format):
    if format == "csv":
        df = pd.read_csv(StringIO(downloaded_blob.content_as_text()))
        df.to_csv(targetPath+blob_name,index = None)
    elif format == "json":
        df = pd.read_json(StringIO(downloaded_blob.content_as_text()))
        df.to_json(targetPath+blob_name)
    elif format == "yaml":
        blob_data = downloaded_blob.content_as_bytes()
        if not os.path.exists(targetPath):
            # if it doesn't exist, create the directory
            os.makedirs(targetPath)
        # Save the YAML file contents to a local file
        with open(targetPath+blob_name, 'wb') as f:
            f.write(blob_data)

def downloadBlob(blob_name,targetPath,format="csv"):
    container_client = __getContainerClient__(account_name,container_name)
    downloaded_blob = container_client.download_blob(os.path.join(targetPath,blob_name))
    parseBlobContent(downloaded_blob,targetPath,blob_name,format)
    return True

def downloadBlobFromAMLStorageContainer(blob_name,targetPath,format="csv"):
    container_client = __getContainerClient__(account_name,azuremlOperations.getAMLContainer())
    downloaded_blob = container_client.download_blob(os.path.join(targetPath,blob_name))
    parseBlobContent(downloaded_blob,targetPath,blob_name,format)
    return True

def uploadDFToBlobStorage(df: pd.DataFrame, account_name: str, container_name: str, blob_name: str, includeIndex=True):
    # Convert the DataFrame to a CSV string
    csv_string = df.to_csv(index=includeIndex)

    # Convert the CSV string to a bytes stream
    csv_bytes = BytesIO(csv_string.encode())

    # Create a BlobServiceClient object
    container_client = __getContainerClient__(account_name,container_name)

    # Upload the CSV file to the container as a blob
    blob_client = container_client.get_blob_client(blob_name)
    blob_client.upload_blob(csv_bytes, overwrite=True)

    logging.info(f"Uploaded DataFrame as CSV to blob '{blob_name}' in container '{container_name}'.")

def moveBlobFromToFolder(source_strgAccountName,dest_strgAccountName,source_container_name,destination_container_name,source_blob_name,destination_blob_name):
    account_key = __getAccountKey__(source_strgAccountName)
    src_blob_service_client = BlobServiceClient(account_url=__getStorageAccountURL__(source_strgAccountName), credential=account_key)
    dest_account_key = __getAccountKey__(dest_strgAccountName)
    dest_blob_service_client = BlobServiceClient(account_url=__getStorageAccountURL__(dest_strgAccountName), credential=dest_account_key)
    # Get source blob client
    
    source_blob_client = src_blob_service_client.get_blob_client(source_container_name, source_blob_name)

    # Create destination blob client
    destination_blob_client = dest_blob_service_client.get_blob_client(destination_container_name, destination_blob_name)

    # Copy blob to destination
    destination_blob_client.start_copy_from_url(source_blob_client.url)

    # Delete the source blob
    source_blob_client.delete_blob()