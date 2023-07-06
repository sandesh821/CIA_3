#Copyright (c) Microsoft. All rights reserved.
from deployment import DeploymentInfraManager as IM
import os
import shutil
import yaml
import ast
import logging
import subprocess
import re
from datetime import datetime

from utilities.azure.azuremlOperations import *
from azureml.core import Environment

userInputs = {}
deploymentConfig = {}

def identifyTargetEnvironment():
    env = IM.DeploymentInfraManager(userInputs)
    return env.getTargetEnvironment()

def __copyAndOverwrite__(from_path, to_path):
    if not os.path.isdir(to_path): 
        os.makedirs(to_path)
    if os.path.exists(to_path):
        shutil.rmtree(to_path)
    shutil.copytree(from_path, to_path)

def __downloadModels__(modelPath,modelType,path):
    print("Downloading training models")
    #===================1.0 Load workspace========================
    ws = getAMLWorkspace()
    ds = ws.get_default_datastore()
    print(modelPath+modelType)
    modelFolder = ds.download(target_path=path, prefix=modelPath+modelType)

def __getAMLEnvironment__(envName):
    ws = getAMLWorkspace()
    details = Environment.get(ws,envName).get_image_details(workspace=ws)
    # print(details["ingredients"]["condaSpecification"])
    return details["dockerImage"]["name"].split("/")[-1]

def __readFile__(path):
    try:
        with open(path, 'r') as file:
            content = file.read()
            file.close()
        return content
    except:
        print("Error in loading file")
        raise

def __updateFile__(outputPath,content):
    try:
        with open(outputPath, 'w') as f:
            f.write(content)
    except:
        print("Error in saving file")
        raise

# Read template config
def __readTemplate__(experimentSet,baseFolder):
    print("Loading template")
    template = __readFile__(baseFolder+experimentSet+"/deploymenttemplate.yaml")
    return template

# Delete Template File
def __delTemplate__(experimentSet,baseFolder):
    print("Deleting template")
    os.remove(baseFolder+experimentSet+"/deploymenttemplate.yaml")

def __updateFileContent__(experimentset,config, pipelineConfig, filePath,baseFolder):
    print("Loading Main file")
    updatedFilePath = baseFolder+experimentset+filePath
    mainFileContent = __readFile__(updatedFilePath)
    mainFileContent = mainFileContent.replace("$$scorescript$$",pipelineConfig.get("entryPoint").replace(".py","").replace("mlcode/",""))
    mainFileContent = mainFileContent.replace("$$storageaccount$$",deploymentConfig.get("sourcestorage"))
    mainFileContent = mainFileContent.replace("$$containername$$",deploymentConfig.get("sourcecontainer"))
    mainFileContent = mainFileContent.replace("$$experimentset$$",experimentset)
    mainFileContent = mainFileContent.replace("$$experiment$$",pipelineConfig.get("experimentTag"))
    mainFileContent = mainFileContent.replace("$$updatedexperimentname$$",config["updatedExpSetName"])
    mainFileContent = mainFileContent.replace("$$experimentsetid$$",str(config["experimentsetid"]))
    
    __updateFile__(updatedFilePath,mainFileContent)

def prepareForDeployment(env,config,pipelineConfig,baseFolder):
    experimentset = pipelineConfig.get("experimentSetName")
    
    srcFolder = baseFolder+env+"Template"
    expDeploymentFolder = baseFolder+experimentset
    __copyAndOverwrite__(srcFolder, expDeploymentFolder)

    updatedExpSetName = (re.sub('[^a-zA-Z0-9 \n\.]', '', experimentset)+config.get("modelName")).lower()
    print(updatedExpSetName)
    if env == "AzureFunction":
        # Change working directory to new folder
        os.chdir(baseFolder+expDeploymentFolder+'/')

        # Generate docker image
        strProcessCall = 'bash script/setup.sh -m '+(updatedExpSetName)+' -t "Timer trigger"'
        subprocess.run(strProcessCall, shell=True)

        # Change working directory to new folder
        os.chdir('../')

    os.makedirs(expDeploymentFolder+"/src/code")
    os.makedirs(expDeploymentFolder+"/src/utilities")

    sourceCodeFolderPath = "platform_code/code/" #"../../platform_code/code/"
    __copyAndOverwrite__(sourceCodeFolderPath+"mlcode", expDeploymentFolder+"/src/code/mlcode")
    __copyAndOverwrite__(sourceCodeFolderPath+"dboperations", expDeploymentFolder+"/src/code/mlcode/dboperations")
    shutil.copy(sourceCodeFolderPath+"masterConfiguration.py", expDeploymentFolder+"/src/code/mlcode/")  

    __copyAndOverwrite__("utilities/", expDeploymentFolder+"/src/utilities")

    config["updatedExpSetName"] = updatedExpSetName

    # Set default path for the source code
    if env == "AzureFunction":
        shutil.copy(sourceCodeFolderPath+pipelineConfig.get("environmentYAMLFile"), expDeploymentFolder+"/src/")
        path = expDeploymentFolder+"/src/func_"+updatedExpSetName+"/"
        __updateFileContent__(experimentset, config,pipelineConfig,path+"__init__.py",baseFolder)
    else:
        path = expDeploymentFolder+"/src/"
        shutil.copy(sourceCodeFolderPath+pipelineConfig.get("environmentYAMLFile"), expDeploymentFolder+"/src/code/")

    # Copy blob reading file
    shutil.copy(baseFolder+"shared/readBlob.py", path) 

    # Copy scoring script file
    shutil.copy(baseFolder+"scoringscripts/"+pipelineConfig.get("entryPoint"), expDeploymentFolder+"/src/code/"+pipelineConfig.get("entryPoint"))

    # Update entry point in main.py
    shutil.copy(baseFolder+"scoringconfig.yaml", path)
    __updateFileContent__(experimentset, config , pipelineConfig, "/src/main.py",baseFolder)

    # Download models
    __downloadModels__(config.get("modelPath"),config.get("modelName"),baseFolder+experimentset+"/src/model")

    if env == "AKS":
        # Update deployment.yaml
        template = __readTemplate__(experimentset,baseFolder)
        template = template.replace("$$acr$$",deploymentConfig["acr"])
        template = template.replace("$$experimentset$$",updatedExpSetName)
        template = template.replace("$$aml$$",deploymentConfig["aml"])
        template = template.replace("$$resourcegroup$$",deploymentConfig["resourcegroup"])
        template = template.replace("$$subscription$$",deploymentConfig["subscription"])
        template = template.replace("$$aksservice$$",deploymentConfig["aksservice"])
        template = template.replace("$$STORAGEACCOUNTNAME$$",deploymentConfig["STORAGEACCOUNTNAME"])
        template = template.replace("$$KEYVAULT$$",deploymentConfig["KEYVAULT"])
        template = template.replace("$$GOLIVESTORAGEACCOUNTNAME$$",deploymentConfig["GOLIVESTORAGEACCOUNTNAME"])
        template = template.replace("$$GOLIVEFUNCTIONAPP$$",deploymentConfig["GOLIVEFUNCTIONAPP"])
        template = template.replace("$$FUNCTIONAPPNAME$$",deploymentConfig["FUNCTIONAPPNAME"])
        template = template.replace("$$podidentityname$$",deploymentConfig["podidentityname"])
        template = template.replace("$$identityname$$",deploymentConfig["identityname"])
        # TODO: Remove this after synchronizing the environment variable names between platform code and utilities
        template = template.replace("$$resourcegroupnameforplatformcode$$",deploymentConfig["resourcegroup"][0])
        template = template.replace("$$subscriptionidforplatformcode$$",deploymentConfig["subscription"][0])
                
        # Convert the forecast time to schedule in AKS
        dt = datetime.strptime(deploymentConfig["forecastTime"],"%H:%M:%S")
        template = template.replace("$$schedule$$",f"{dt.minute} {dt.hour} * * *")
        outputPath = baseFolder+experimentset+"/deployment.yaml"
        __updateFile__(outputPath,template)

        # Remove template file
        __delTemplate__(experimentset,baseFolder)

    return updatedExpSetName

def deploy(configName,deploymentConfigurations,userSelections,baseFolder="./"):
    global deploymentConfig, userInputs

    deploymentConfig = deploymentConfigurations
    userInputs = userSelections
    #===================Load configurations===================
    try:
        with open(baseFolder+configName, 'r') as file:
            confg = yaml.safe_load(file)
    except (IOError, ValueError, EOFError, FileNotFoundError) as ex:
        logging.error("Config file not found")
        logging.error(ex)
        raise ex
    except Exception as YAMLFormatException:
        logging.error("Config file not found")
        logging.error(YAMLFormatException)
        raise YAMLFormatException
    scoring_config = str(confg.get('ScoringConfig',{}))
    scoring_config_parsed = ast.literal_eval(scoring_config)
    scoring_pipeline_config = str(confg.get('ScoringPipelineConfig',{}))
    scoring_pipeline_config_parsed = ast.literal_eval(scoring_pipeline_config)

    #==========================================================
    experimentSet = scoring_pipeline_config_parsed.get("experimentSetName")
    modelName = scoring_config_parsed["modelName"]
    userInputs["modelname"] = modelName
    env = identifyTargetEnvironment()
    print("Identified Environment: ", env)
    
    scoring_config_parsed["experimentsetid"] = deploymentConfig["experimentsetid"]
    updatedExpSetName = prepareForDeployment(env,scoring_config_parsed,scoring_pipeline_config_parsed,baseFolder)

    # Change working directory to new folder
    os.chdir(baseFolder+experimentSet+'/')

    envYAML = scoring_pipeline_config_parsed.get("environmentYAMLFile")
    environment = scoring_pipeline_config_parsed.get("environmentName")

    logging.info("Building docker image")
    # Generate docker image
    if env == "AzureFunction":
        strProcessCall1 = 'bash script/buildDocker.sh -a '+deploymentConfig.get("acr").lower()+' -r '+updatedExpSetName + " -e "+envYAML+" -m "+deploymentConfig["aml"] +" -g "+deploymentConfig["resourcegroup"] +" -s "+deploymentConfig["subscription"] 
        subprocess.run(strProcessCall1, shell=True)
    else:
        strProcessCall1 = 'bash script/buildDocker.sh -a '+deploymentConfig.get("acr").lower()+' -r '+updatedExpSetName + " -e "+envYAML+" -d "+__getAMLEnvironment__(environment) 
        subprocess.run(strProcessCall1, shell=True)

        logging.info("Start: Deploying to AKS")
        # Trigger deployment for selected environment
        strProcessCall2 = 'bash script/deployToAKS.sh -s "'+deploymentConfig.get("subscription")+'" -r "'+deploymentConfig.get("resourcegroup")+'" -a "'+deploymentConfig.get("aksservice")+'" -n "'+updatedExpSetName+'" -c "deployment.yaml" -i "'+deploymentConfig.get("identityname") + '"'
        print(strProcessCall2)
        subprocess.run(strProcessCall2, stdin=None, stdout=None, stderr=None, shell=True, close_fds=True)
        logging.info("End: Deploying to AKS")