#Copyright (c) Microsoft. All rights reserved.
import shutil
import os
import sys
import logging
import pandas as pd
import datetime
sys.path.append(os.getcwd())
from utilities.azure import blobOperations
from utilities.fileoperations import fileoperations
from utilities.dboperations import dboperations
from workflow.common import getdata
from golive import goliveappconfig

def insertPredictionSchedule(data, forecastDetails):
    logging.info("Inserting prediction schedule")
    dboperations.executeStoredProcedure("usp_insertPredictionSchedule","@ExperimentSetID =?,@PredictionDate=?",(data["experimentsetid"],(datetime.datetime.now().strftime("%Y-%m-%d ")+forecastDetails["ForecastTime"])),"golive",0)

def uploadTrainingData():
    logging.info("Uploading training data")
    # Read training file and save as masterfile in master folder
    try:
        trainingFilePath = goliveappconfig.trainingSourceDataPath

        _,trainingdf,_ = blobOperations.getBlobDf(goliveappconfig.trainingSourceStorageAccount,goliveappconfig.trainingSourceContainerName,trainingFilePath)
        blobOperations.uploadDFToBlobStorage(trainingdf, goliveappconfig.sourceStorageAccount,goliveappconfig.sourceMasterDataContainerName,goliveappconfig.filePathPrefix+"/masterdata.csv",False)
    except Exception as e:
        logging.info(f"Error while uploading training data: {e}")
        logging.info(f"Training file path: {trainingFilePath}")
        logging.info(f"Training storage account: {goliveappconfig.trainingSourceStorageAccount}")
        logging.info(f"Training container name: {goliveappconfig.trainingSourceContainerName}")
        raise Exception(f"Error while uploading training data: {e}")
    
    try:
        # Upload scoring file
        _,scoreDF,_ = blobOperations.getBlobDfFromAMLStorageContainer(goliveappconfig.scoringDataPath)
        scoreDF = scoreDF[goliveappconfig.colList]
        blobOperations.uploadDFToBlobStorage(scoreDF, goliveappconfig.sourceStorageAccount,goliveappconfig.sourceMasterDataContainerName,goliveappconfig.filePathPrefix+"/batchscoring.csv",False)
    except Exception as e:
        logging.info(f"Error while uploading scoring data: {e}")
        logging.info(f"Scoring file path: {goliveappconfig.scoringDataPath}")
        logging.info(f"Scoring storage account: {goliveappconfig.sourceStorageAccount}")
        logging.info(f"Scoring container name: {goliveappconfig.sourceMasterDataContainerName}")
        raise Exception(f"Error while uploading scoring data: {e}")

def createFunctionFromTemplate(data, eventDF,forecastDetails):
    logging.info("Updating function template") 
    experimentSetName = data["experimentsetname"]
    appName = f"golive_{experimentSetName}App"
    targetFolder = "golive/"+appName
    fileoperations.__copyAndOverwrite__("golive/MlOpsAutomation/functionAppTemplate",targetFolder)
    # Update the folder paths in blob triggers
    fileContent = fileoperations.__readFile__(f"{targetFolder}/DataValidation/function.json")
    fileContent = fileContent.replace("$$streamingcontainer$$",goliveappconfig.sourceStreamingDataContainerName)
    fileoperations.__updateFile__(f"{targetFolder}/DataValidation/function.json",fileContent)

    driftFilePath = f"{targetFolder}/DataDriftValidation/function.json"
    fileContent = fileoperations.__readFile__(driftFilePath)
    fileContent = fileContent.replace("$$experimentsetname$$",goliveappconfig.experimentSetName)
    fileContent = fileContent.replace("$$experimenttag$$",goliveappconfig.experimentTag)
    fileContent = fileContent.replace("$$internalrunid$$",goliveappconfig.internalRunID)
    fileoperations.__updateFile__(driftFilePath,fileContent)

    # Update schedule in retraining
    try:
        retrainingPath = f"{targetFolder}/ModelRetraining/function.json"
        fileContent = fileoperations.__readFile__(retrainingPath)
        
        if eventDF["modelRetrainTime"] is None:
            fileContent = fileContent.replace("$$disabled$$","true")
        else:
            fileContent = fileContent.replace("$$disabled$$","false")
            # Get schedule from inputs
            retrainDayMonth = int(eventDF["modelRetrainTime"])
            if eventDF["modelRetrainUnit"] == "D":
                # Schedule to run 
                schedule = f'0 0 0 */{retrainDayMonth} * *'
            elif eventDF["modelRetrainUnit"] == "M":
                schedule = f'0 0 0 1 */{retrainDayMonth} *'
                
        fileContent = fileContent.replace("$$schedule$$",schedule)
        fileoperations.__updateFile__(retrainingPath,fileContent)
    except:
        logging.info("Retraining not scheduled")
        pass
    # Update schedule for api refresh and appending streaming data modules
    # Convert to time object
    time_obj = pd.to_datetime(forecastDetails["ForecastTime"], format="%H:%M:%S")-datetime.timedelta(minutes=30)
    hour = time_obj.hour
    min = time_obj.minute
    schedule = f"* {min} {hour} * * *"

    apiPath = f"{targetFolder}/APIDataManager/function.json"
    fileContent = fileoperations.__readFile__(apiPath)
    fileContent = fileContent.replace("$$schedule$$",schedule)
    fileoperations.__updateFile__(apiPath,fileContent)

    appendPath = f"{targetFolder}/AppendStreamingData/function.json"
    fileContent = fileoperations.__readFile__(appendPath)
    fileContent = fileContent.replace("$$schedule$$",schedule)
    fileoperations.__updateFile__(appendPath,fileContent)

    return appName

def copyRequiredFolders(data):
    experimentSetName = data["experimentsetname"]
    targetFolder = f"golive/golive_{experimentSetName}App"
    fileoperations.__copyAndOverwrite__("golive/MlOpsAutomation/scripts",targetFolder+"/golive/MlOpsAutomation/scripts")
    fileoperations.__copyAndOverwrite__("golive/modules",targetFolder+"/modules")
    fileoperations.__copyAndOverwrite__("utilities",targetFolder+"/utilities")
    # fileoperations.__copyAndOverwrite__("deployment",targetFolder+"/deployment")
    fileoperations.__copyAndOverwrite__("workflow",targetFolder+"/workflow")
    # fileoperations.__copyAndOverwrite__("platform_code",targetFolder+"/platform_code")
    shutil.copy("golive/goliveappconfig.py", targetFolder+"/")

def setup(data,eventDF,forecastDetails):
    if data["fileUpload"]:
        # Upload training data as masterdata 
        uploadTrainingData()
        # Initialize prediction schedule
        insertPredictionSchedule(data, forecastDetails)

        logging.info("Training data uploaded")

    appName = createFunctionFromTemplate(data,eventDF,forecastDetails)
    logging.info("Template updated")
    copyRequiredFolders(data)
    logging.info("Folders copied")

    return appName