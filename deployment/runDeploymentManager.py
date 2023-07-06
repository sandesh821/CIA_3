#Copyright (c) Microsoft. All rights reserved.
import shutil
import json
import logging
from utilities import config
from utilities.azure import blobOperations
from deployment import deploymentManager
from workflow.common import getdata

def triggerDeploymentManager(data, type="best"):
    # Get Model Deployment Configurations
    deployConfig = getdata.getModelDeploymentConfigurations(data,"golive")
    # Get Forecast Detailsa
    forecastDetails = getdata.getForecastSetupDetails(data)
    # Get Best Model Details
    selectedModel = getdata.getModelDetails(data,type)

    logging.info("Download scoringConfig.yaml file")
    yamlFile = selectedModel["Experiment"]+".yaml"
    filePath = f'outputs/{data["experimentsetname"]}/{selectedModel["Experiment"]}/{selectedModel["InternalRunId"]}/'

    # Download scoringConfig.yaml file for the best model
    blobOperations.downloadBlobFromAMLStorageContainer(yamlFile,filePath,format="yaml")

    # Define static path for golive code folder
    baseFolder = "deployment/"
    scoringConfigPath = "scoringconfig.yaml"


    # Read scoringConfig from yaml file
    shutil.copy(filePath+yamlFile, baseFolder+scoringConfigPath) 

    if deployConfig is not None and len(deployConfig) > 0:
        logging.info("Preparing deployment configurations")
        deployConfig = json.loads(deployConfig[0]["deploymentManagerConfig"])
        userInputs = {
                "acceleratortype": deployConfig["acceleratortype"],
                "modeltype" : deployConfig["modelType"],
                "cost" : deployConfig["cost"],
                "versiondependency" : deployConfig["versiondependency"],
                "horizon" : forecastDetails["ForecastHorizon"].values[0],
                "hostingmodel" : deployConfig["hostingmodel"]
            }

        deploymentConfig = {
                "acr" : config.ACR,
                "subscription" : config.SUBSCRIPTIONID[0],
                "resourcegroup" : config.RESOURCEGROUP[0],
                "aksservice" : config.AKSSERVICE,
                "aml" : config.AMLWORKSPACENAME,
                "sourcestorage" : config.GOLIVESTORAGEACCOUNTNAME,
                "sourcecontainer" : "masterdata",                    
                "forecastTime" : forecastDetails["ForecastTime"].values[0],
                "experimentsetid" : data["experimentsetid"],
                "STORAGEACCOUNTNAME": config.STORAGEACCOUNTNAME,
                "KEYVAULT": config.KEYVAULT,
                "GOLIVESTORAGEACCOUNTNAME": config.GOLIVESTORAGEACCOUNTNAME,
                "GOLIVEFUNCTIONAPP": config.GOLIVEFUNCTIONAPP,
                "FUNCTIONAPPNAME": config.FUNCTIONAPPNAME,
                "podidentityname" : config.podidentityname,
                "identityname": config.identityname
            }
        logging.info("Preparing deployment folder structure")
        # Create deployment folder structure
        deploymentManager.deploy(scoringConfigPath,deploymentConfig,userInputs,baseFolder)