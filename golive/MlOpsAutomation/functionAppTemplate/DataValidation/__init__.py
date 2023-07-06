#Copyright (c) Microsoft. All rights reserved.
import logging
import pandas as pd
import azure.functions as func

from modules.datavalidation import datavalidation
from utilities.azure import blobOperations
from utilities.dboperations import dboperations
from utilities.emailNotification import sendmail
import goliveappconfig

def main(myblob: func.InputStream):
    logging.info(f"New file uploaded \n"
                 f"Name: {myblob.name}\n")
    data = pd.read_csv(myblob)
    logging.info(data)

    logging.info(goliveappconfig.experimentSetId)
    
    blob_name = myblob.name.split("/")[-1]
    source_folder_name = myblob.name.replace((goliveappconfig.sourceStreamingDataContainerName+'/') ,"")
    if(goliveappconfig.iotFileIdentifier in myblob.name):
        destination_folder_name = f"{goliveappconfig.filePathPrefix}/iot/{blob_name}"
    elif(goliveappconfig.entityFileIdentifier in myblob.name):
        destination_folder_name = f"{goliveappconfig.filePathPrefix}/entity/{blob_name}"
        
    # Validate the input file
    if not datavalidation.basicDataValidation(data):
        logging.error("Data validation failed")
        # Send notification
        sendmail.EmailNotification('Alert: Data validation failed',f'Basic Data validation failed for file {blob_name}',goliveappconfig.tolist,goliveappconfig.smtpServer,goliveappconfig.smtpPort)

        # Move file to bad file folder if basic validation fails
        blobOperations.moveBlobFromToFolder(goliveappconfig.sourceStreamingStorageAccount,goliveappconfig.sourceStorageAccount,goliveappconfig.sourceStreamingDataContainerName, goliveappconfig.sourceBadDataContainerName,source_folder_name,destination_folder_name)
    else:
        logging.info("File validated")

        # Move file to iot folder if basic validation succeeds
        blobOperations.moveBlobFromToFolder(goliveappconfig.sourceStreamingStorageAccount,goliveappconfig.sourceStorageAccount,goliveappconfig.sourceStreamingDataContainerName,goliveappconfig.sourceRawDataContainerName,source_folder_name,destination_folder_name)
        logging.info("File moved")