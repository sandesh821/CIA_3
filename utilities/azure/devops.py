import requests
import json
from utilities.azure import keyvaultOperations
from utilities import config

def generateDevOpsRequest(buildid,data):
    
    url = config.DevOpsURL.replace("$$buildid$$",str(buildid))

    (access_token) = keyvaultOperations.getSecrets(['patToken'])
    print(data)
    payload = json.dumps({
        "resources": {
            "repositories": {
                "self": {
                    "refName": "refs/heads/"+config.DevOpsBranchName
                }
            }
        },
        "templateParameters": {
                               'experimentsetid': data["experimentsetid"],
                               'experimentsetname': data["experimentsetname"], 
                               'fileUpload': data["fileUpload"],
                               'deploymentType': data["deploymentType"]
                               }
        })
    headers = {'Content-Type': 'application/json'}
    auth = ('', eval(access_token[0]))

    response = requests.post(url, headers= headers, data=payload, auth=auth)
    if response.status_code == 200:
        # Print the response from the function
        print(response.text)
        print("Request submitted")
    else:
        print("Request submission failed")
        print(response.status_code)
        print(response.text)
        print(response.content)