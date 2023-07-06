#Copyright (c) Microsoft. All rights reserved.
import sys
import os
import shutil
import json
import logging
import requests
from utilities import config
currentDir = os.path.dirname(os.path.abspath(os.path.join(__file__,"../..")))
sys.path.insert(0,currentDir)
from utilities.azure import blobOperations
from utilities.azure import keyvaultOperations
from utilities.emailNotification import sendmail
# from utilities.azure import accessToken

# print(accessToken.getAccessToken())

tolist = ["asthaagarwal@microsoft.com"]
sendmail.EmailNotification('testsubject','testbody',tolist)

# # Get master key from keyvault
# secrets = keyvaultOperations.getSecrets(["functionAppMasterKey"])
# masterKey = secrets[0]
# headers = {"x-functions-key": masterKey,"Content-Type": "application/json"}
# endpoint_url = f"https://eventManagerFunctionApp.azurewebsites.net/admin/functions/ModelRetraining/"

# # Make the request to the endpoint URL
# response = requests.post(endpoint_url, headers= headers, data="{}")
# if response.status_code == 202:
#     # Print the response from the function
#     print(response.text)
#     print("Retraining request submitted")
# else:
#     print("Retraining trigger failed, HTTP response ")
#     print(response.status_code)
#     print(response.reason)
#     print(response.content)
# # print(currentDir)

# print(getStorageAccountList())
# print(getContainerList("azuremlforecas1459952141"))
# print(getContainerList("streamingmasterdata"))

# downloadBlobFromAMLStorageContainer("experiment21.yaml","outputs/HornsdaleDemo/experiment21/20230428100540/",format="yaml")

