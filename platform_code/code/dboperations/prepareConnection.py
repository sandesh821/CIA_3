#Copyright (c) Microsoft. All rights reserved.

import sys
import os
import logging
currentDir = os.path.dirname(os.path.abspath(os.path.join(__file__,"..")))
sys.path.insert(0,currentDir)

import dboperations.config as config
from masterConfiguration import azureDetails

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from azureml.core import Workspace
from azureml.core import Run
from azureml.exceptions import UserErrorException

def getKeyVault():
    try:
        keyvault = azureDetails["KEYVAULT"]
        credential = DefaultAzureCredential()
        Vault_url="https://"+keyvault+".vault.azure.net/"
        print(Vault_url)
        secret_client = SecretClient(vault_url=Vault_url, credential=credential)
    except Exception as ex:
        print("Connection to keyvault failed")
        print(ex)
    print(secret_client)
    return secret_client

def getAMLWorkspace():
    try:
        logging.info("Reading from config")
        ws = Workspace.from_config()
    except AttributeError as ex:
        logging.info("Reading from run context")
        current_run = Run.get_context()
        ws = current_run.experiment.workspace
    except UserErrorException as ex:
        try:
            logging.info("Reading from run context")
            current_run = Run.get_context()
            ws = current_run.experiment.workspace
        except Exception as ex:
            logging.info(ex)
            logging.info("Reading from master config")
            print("Reading from master config in platform code")
            ws = Workspace.get(name=azureDetails["AMLWORKSPACENAME"],
                subscription_id=azureDetails["SUBSCRIPTIONID"],
                resource_group=azureDetails["RESOURCEGROUP"])    
    except Exception as ex:
        logging.info(ex)
        logging.info("Reading from master config")
        ws = Workspace.get(name=azureDetails["AMLWORKSPACENAME"],
            subscription_id=azureDetails["SUBSCRIPTIONID"],
            resource_group=azureDetails["RESOURCEGROUP"])
    return ws

def getSecrets():
    try:
        client = getKeyVault()
        print("Key vault client initialized")
        logging.info("Key vault client initialized")
        username = client.get_secret(config.sqluserKey).value
        pwd = client.get_secret(config.sqlpwdKey).value
        server = client.get_secret(config.serverKey).value 
        database = client.get_secret(config.databaseKey).value  
    except Exception as ex:
        print("Reading Key vault details from AML workspace")
        logging.info("Reading Key vault details from AML workspace")
        try:
            ws = getAMLWorkspace()
            keyvault = ws.get_default_keyvault()
            logging.info("Key vault client initialized from AML")
            username = keyvault.get_secrets([config.sqluserKey]).get(config.sqluserKey)
            pwd = keyvault.get_secrets([config.sqlpwdKey]).get(config.sqlpwdKey)
            server = keyvault.get_secrets([config.serverKey]).get(config.serverKey)
            database = keyvault.get_secrets([config.databaseKey]).get(config.databaseKey)
        except Exception as ex:
            logging.error(ex)
            logging.error("Error in reading secrets from inside platform code!")
    return username, pwd, server, database

def getConnectionString():
    username, pwd, server, database = getSecrets()
    connection = config.connectionString
    connection = connection.replace("$$username$$",username).replace("$$password$$",pwd)
    connection = connection.replace("$$server$$",server).replace("$$database$$",database)
    return connection

# Test script
if __name__ == "__main__":
    getConnectionString()

    

