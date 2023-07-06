#Copyright (c) Microsoft. All rights reserved.
import json
import os
import sys
import subprocess
import logging
sys.path.append(os.getcwd())
from utilities.fileoperations import fileoperations
from utilities.config import *
from workflow.common import getdata

def getForecastDetails(data):
    # Read training file and save as masterfile in master folder
    forecastDetails = getdata.getForecastSetupDetails(data)
    return forecastDetails.to_dict(orient="records")[0]

def updateGoLiveConfigurations(data,selectedModelDetails,dataIngestionDF,forecastDetails,selectedExperiment,eventDF, notificationConfigurations):
    logging.info("Updating experiment details in goliveappconfig.py")
    fileContent = fileoperations.__readFile__("golive/goliveappconfigtemplate.py")
    fileContent = fileContent.replace("'$$experimentSetId$$'",str(data["experimentsetid"]))
    fileContent = fileContent.replace("$$experimentSetName$$",data["experimentsetname"])
    fileContent = fileContent.replace("$$experimentTag$$",selectedModelDetails["Experiment"])
    fileContent = fileContent.replace("$$internalRunID$$",str(selectedModelDetails["InternalRunId"]))
    fileContent = fileContent.replace("$$modelName$$",str(selectedModelDetails["ModelName"]))
    
    logging.info("Updating source data details in goliveappconfig.py")
    SourceDataDetails = json.loads(dataIngestionDF["SourceDataDetails"].values[0])
    ApiMapping = json.loads(dataIngestionDF["ApiMapping"].values[0])
    DataRefreshDetails = json.loads(dataIngestionDF["DataRefreshDetails"].values[0])
    fileContent = fileContent.replace("$$goliveStreamingStorageAccount$$",SourceDataDetails["goliveStorageAccount"])
    fileContent = fileContent.replace("$$goliveStreamingDataContainer$$",SourceDataDetails["goliveContainer"])
    fileContent = fileContent.replace("$$goliveworkflowStorageAccount$$",GOLIVESTORAGEACCOUNTNAME)
    fileContent = fileContent.replace("$$trainingSourceStorageAccount$$",STORAGEACCOUNTNAME)

    logging.info("Updating data ingestion details in goliveappconfig.py")
    for file in DataRefreshDetails:
        if file["goLiveIsIoT"] is not None and len(file["goLiveIsIoT"]) != 0:
            fileContent = fileContent.replace("$$iotFileIdentifier$$",file["goLiveFile"])
        elif file["goLiveIsIoTEnitity"] is not None and len(file["goLiveIsIoTEnitity"]) !=0:
            fileContent = fileContent.replace("$$entityFileIdentifier$$",file["goLiveFile"])
    if len(ApiMapping):
        apiIdentifier = ApiMapping["goLiveFile"]
        api = ApiMapping["goLiveAPIType"]
        apijson = {apiIdentifier : api}
        fileContent = fileContent.replace("'$$apidata$$'",json.dumps(apijson))

    logging.info("Updating forecast details in goliveappconfig.py")
    # Update forecast details
    fileContent = fileContent.replace("$$forecastTime$$",str(forecastDetails["ForecastTime"]))
    fileContent = fileContent.replace("'$$forecastHorizon$$'",str(forecastDetails["ForecastHorizon"]))
    fileContent = fileContent.replace("$$forecastGranularity$$",str(forecastDetails["Granularity"])+forecastDetails["GranularityUnits"])
    fileContent = fileContent.replace("$$forecastInitialwindow$$",str(forecastDetails["InitialWindowSteps"])+forecastDetails["InitialWindowStepsUnits"])
    fileContent = fileContent.replace("'$$lookback$$'",str(forecastDetails["Lookback"]))
    fileContent = fileContent.replace("$$forecastTimezone$$",str(forecastDetails["TimeZone"]))

    logging.info("Updating data drift details in goliveappconfig.py")
    # Update drift threshold values
    fileContent = fileContent.replace("'$$cat_col_threshold$$'",str(eventDF["catColThreshold"]))
    fileContent = fileContent.replace("'$$num_col_threshold$$'",str(eventDF["numColThreshold"]))
    if "historyEnabled" in eventDF.keys():
        fileContent = fileContent.replace("'$$historyEnabled$$'",str(eventDF["historyEnabled"])) 
    else:
        fileContent = fileContent.replace("'$$historyEnabled$$'",str(False))    

    logging.info("Updating experiment configurations in goliveappconfig.py")
    # Update covariate and columns
    fileContent = fileContent.replace("'$$pastCovariates$$'",selectedExperiment["PastCovariates"])
    fileContent = fileContent.replace("'$$futureCovariates$$'",selectedExperiment["FutureCovariates"])
    fileContent = fileContent.replace("'$$colList$$'",selectedExperiment["FeatureList"])
    
    # Update function app name in configuration
    fileContent = fileContent.replace("$$functionAppName$$",FUNCTIONAPPNAME)

    # Notification configurations
    logging.info("Updating notification configurations in goliveappconfig.py")
    # print(notificationConfigurations)
    fileContent = fileContent.replace("'$$tolist$$'",str(notificationConfigurations["receiversList"].split(",")))
    fileContent = fileContent.replace("'$$smtpPort$$'",notificationConfigurations["smtpPort"])
    fileContent = fileContent.replace("$$smtpServer$$",notificationConfigurations["smtpServer"])
    notificationConfigurations

    fileoperations.__updateFile__("golive/goliveappconfig.py",fileContent)

def setup(data, type="best"):
    try:
        selectedModel = getdata.getModelDetails(data,type)

        # Get Data Ingestion details
        dataIngestionDF = getdata.getDataIngestionDetails(data)

        # Get Event Configuration details
        eventDF = getdata.getEventConfigurationDetails(data)

        notificationConfigurations = getdata.getNotificationConfigurations(data)

        # Get Forecast Details
        forecastDetails = getForecastDetails(data)

        # Get Experiment Details
        experimentConfigurationDetails = getdata.getSavedExperiments(data)
        selectedExperiment = [x for x in experimentConfigurationDetails if x['ExperimentTag'] == selectedModel["Experiment"]]
        # print(selectedExperiment)
        # Update goliveapp config
        updateGoLiveConfigurations(data,selectedModel,dataIngestionDF,forecastDetails,selectedExperiment[0],eventDF,notificationConfigurations)
        print('Go live configuration prepared')
        # Invoke Function App setup
        from golive.MlOpsAutomation.scripts import setupFunctionApp
        appName = setupFunctionApp.setup(data,eventDF,forecastDetails)
        print('Go live configuration completed')

        strProcessCall = 'bash golive/'+appName+'/buildDocker.sh -a '+ACR.lower()+' -r '+GOLIVEFUNCTIONAPP + ' -m '+FUNCTIONAPPNAME+' -g '+RESOURCEGROUP[0]
        print(strProcessCall)
        subprocess.run(strProcessCall, stdin=None, stdout=None, stderr=None, shell=True, close_fds=True)

        return True
    except Exception as e:
        logging.error(e)
        return False

if __name__ == '__main__':
    data = {
        "experimentsetid":38,
        "experimentsetname" : "HornsdaleDemo"
    }
    setup(data)
    