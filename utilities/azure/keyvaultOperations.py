#Copyright (c) Microsoft. All rights reserved.
from azureml.core import Workspace
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
import utilities.config as config 
import logging

def getAMLWorkspace():
    try:
        ws = Workspace.from_config()
    except Exception as ex:
        ws = Workspace.get(name=config.AMLWORKSPACENAME,
               subscription_id=config.SUBSCRIPTIONID[0],
               resource_group=config.RESOURCEGROUP[0])
    return ws

def getKeyVault():
    try:
        keyvault = config.KEYVAULT
        credential = DefaultAzureCredential()
        Vault_url="https://"+keyvault+".vault.azure.net/"
        print(Vault_url)
        secret_client = SecretClient(vault_url=Vault_url, credential=credential)
    except Exception as ex:
        print("Connection to keyvault failed")
        print(ex)
    print(secret_client)
    return secret_client

def getSecrets(keys):
    values = []
    try:
        client = getKeyVault()
        print("Key vault client initialized")
        logging.info("Key vault client initialized")
        for key in keys:
            values.append(client.get_secret([key]).value)
    except Exception as ex:
        print("Key vault client cannot be accessed using managed identity to connect to Key vault")
        logging.info("Key vault client cannot be accessed using managed identity to connect to Key vault")
        try:
            ws = getAMLWorkspace()
            keyvault = ws.get_default_keyvault()
            for key in keys:
                values.append(keyvault.get_secrets([key]).get(key))
        except Exception as ex:
            logging.error(ex)
            print(ex)
            print("Error in reading secrets from utilities!")
    return tuple(values)