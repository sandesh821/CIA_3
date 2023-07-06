#Copyright (c) Microsoft. All rights reserved.
import warnings
warnings.filterwarnings("ignore")

import adal
import requests
import json
import pandas as pd
from azureml.core import Workspace
from azureml.core import Run
from azure.cli.core import get_default_cli
import pandas as pd
import multiprocessing
import psutil
import time, datetime
import tempfile
from azureml.core import ComputeTarget
import time
import re
import logging

class AMLOperations():
    def __init__(self,params):
        self.geography = params.get("geography")
        self.AMLWORKSPACENAME = params.get("AMLWORKSPACENAME")
        self.RESOURCEGROUP = params.get("RESOURCEGROUP")
        self.subscriptionid =  params.get("SUBSCRIPTIONID")
        
        self.__getAMLWorkspace__()
        self.__azcliLogin__()
        self.__getAccessToken__()
        # Prepare base list of workspace computes and parent vm size list
        self.__getLocationNames__()
        self.__getVMSizeList__()        

    def __getsubscriptionid__(self):
        keyvault = self.ws.get_default_keyvault()
        self.subscriptionid = keyvault.get_secrets(['subscriptionid']).get('subscriptionid')
        return self.subscriptionid

    def __getAMLWorkspace__(self):
        try:
            ws = Workspace.from_config()
        except Exception as ex:
            ws = Workspace.get(name=self.AMLWORKSPACENAME,
            subscription_id=self.subscriptionid,
            resource_group=self.RESOURCEGROUP)

        self.ws = ws
        self.workspaceName = ws.get_details().get("name")
        self.workspaceId = ws.get_details().get("id")
        self.resourceGroupName = self.workspaceId.lstrip("/").split("/")[3]
        return ws

    def __getAccessToken__(self):
        keyvault = self.ws.get_default_keyvault()
        secrets = keyvault.get_secrets(['clientid','clientsecret','tenantid'])

        #Get Bearer token
        authheaders = {
                "Host": "login.microsoftonline.com",
                "Content-Type": "application/x-www-form-urlencoded"
            }

        data = {
            "grant_type": "client_credentials",
            "client_id": secrets['clientid'],
            "client_secret": secrets['clientsecret'],
            "scope": 'https://management.azure.com/.default'
        }

        uri = "https://login.microsoftonline.com/" + secrets['tenantid'] + "/oauth2/v2.0/token"
        restoken = requests.get(url=uri,data=data, headers = authheaders)
        jsontoken = json.loads(restoken.text)
        access_token = jsontoken['token_type'] + ' ' + jsontoken['access_token']

        self.access_token = access_token
        return access_token

    def __getLocationNames__(self):
        #Get loacation names
        url = 'https://management.azure.com/subscriptions/' + self.subscriptionid + '/locations?api-version=2020-01-01'
        headers = {'Content-Type': 'application/json',
        'Authorization': self.access_token}

        resploc = requests.get(url=url,headers = headers)
        data = json.loads(resploc.text)
        # Geography Group and Location Name 
        names =[]

        dfLocations = pd.DataFrame(columns = ['geographyGroup','location'])
        for tag in data["value"]:
            try:
                geographyGroup = tag["metadata"]["geographyGroup"]
                if geographyGroup == self.geography:
                    names.append(tag["name"])
            except:
                a=1

        self.locations = names
        return names
    
    def __azcli__ (self,args_str):
        temp = tempfile.TemporaryFile(mode = "r+")
        args = args_str.split()
        cli = get_default_cli()
        cli.invoke(args, out_file=temp)
        if cli.result.result:
            return cli.result.result
        elif cli.result.error:
            raise cli.result.error
        return True

    def __azcliLogin__(self):
        keyvault = self.ws.get_default_keyvault()
        secrets = keyvault.get_secrets(['clientid','clientsecret','tenantid'])
        self.__azcli__("login --service-principal -u " + secrets['clientid'] + " -p " + secrets['clientsecret'] + " --tenant " + secrets['tenantid'])
        
    def __getVMSizeList__(self):
        self.dfSupportedVMs = pd.DataFrame(columns=['name', 'numberOfCores', 'osDiskSizeInMb', 'resourceDiskSizeInMb', 'memoryInMb', 'maxDataDiskCount','location'])
        for name in self.locations:
            try:
                supportedvms = self.__azcli__("vm list-sizes --output table --location '" + name + "'")
                dfVMs = pd.DataFrame(supportedvms)
                dfVMs['location'] = name
                dfVMs['name'] = dfVMs['name'].str.upper()
                self.dfSupportedVMs = self.dfSupportedVMs.append(dfVMs)
            except Exception as ex:
                logging.info(ex)

        self.dfSupportedVMs.rename(columns={'name':'vmSize'}, inplace=True) 
    
    def __getCapacities__(self):
        dfCapacity = pd.DataFrame(columns = ['Location', 'AvailableCapacity'])
        compute_bucket = []
        
        for name in self.locations:
            url = 'https://management.azure.com/subscriptions/'+ self.subscriptionid +'/providers/Microsoft.Capacity/resourceProviders/Microsoft.Compute/locations/' + name + '/serviceLimits/cores?api-version=2020-10-25'
            headers = {'Content-Type': 'application/json',
            'Authorization': self.access_token}

            OverallCapacity = 0
            Used = 0
            AvailableCapacity = 0

            response = requests.get(url=url,headers = headers)
            if response.status_code == 200 :
                respjson = json.loads(response.text)
                OverallCapacity = respjson['properties']['limit']
                Used = respjson['properties']['currentValue']
                AvailableCapacity = OverallCapacity - Used
                compute_bucket.append(AvailableCapacity)
                row = pd.Series([name, AvailableCapacity], index=dfCapacity.columns)
                dfCapacity = dfCapacity.append(row,ignore_index=True)

        dfCapacity = dfCapacity.sort_values(by='AvailableCapacity', ascending=False)
        self.location_bucket = dfCapacity.iloc[:,0].tolist()
        self.compute_bucket = dfCapacity.iloc[:,1].tolist()

        return self.location_bucket,self.compute_bucket

    def __getWorkspaceComputes__(self):
        dfComputes = pd.DataFrame(columns = ['computeType','name', 'location', 'vmSize', 'idleNodeCount','runningNodeCount'])
        compute_bucket = []
        computeLength = 0
        url = 'https://management.azure.com/'+self.workspaceId+'/computes?api-version=2022-10-01&$skip=0'
        flag = True
        while(flag):
            headers = {'Content-Type': 'application/json',
            'Authorization': self.access_token}
            response = requests.get(url=url,headers = headers)
            if response.status_code == 200 :
                respjson = json.loads(response.text)
                computeLength = computeLength + 10
                if ("nextLink" not in respjson.keys()):
                    flag = False
                else:
                    url = respjson["nextLink"]+'&$skip='+str(computeLength)
                    
                fullComputeList = respjson["value"]
                
                if(fullComputeList == 0):
                    break
                for compute in fullComputeList:
                    computeProperties = compute["properties"]
                    if(computeProperties["computeType"] == "AmlCompute"):
                        new_row = pd.DataFrame({'computeType': computeProperties["computeType"], 'name': compute["name"], 'location': computeProperties["computeLocation"],'vmSize':str(computeProperties["properties"]['vmSize']),'idleNodeCount': computeProperties["properties"]["nodeStateCounts"]["idleNodeCount"],'runningNodeCount': computeProperties["properties"]["nodeStateCounts"]["runningNodeCount"],'nodeIdleTimeBeforeScaleDown': computeProperties["properties"]["scaleSettings"]["nodeIdleTimeBeforeScaleDown"]}, index=[0])
                        dfComputes = pd.concat([new_row,dfComputes.loc[:]]).reset_index(drop=True)
         
        dfComputes.index = list(dfComputes.index)
        
        dfComputes["vmSize"] = dfComputes["vmSize"].astype(str)
        self.dfSupportedVMs["vmSize"] = self.dfSupportedVMs["vmSize"].astype(str)
        
        mergedComputeList = dfComputes.merge(self.dfSupportedVMs, on=["location","vmSize"],how="inner",suffixes=('', '_right'))
        
        self.computes = mergedComputeList[dfComputes.columns.values.tolist()+["numberOfCores"]]
        
    def __getComputeScaleDownIdleSeconds__(self, idleSecondsPT):
        #TO DO: Convert the below code into RegEx
        hr = min = sec = 0

        if (idleSecondsPT.__contains__('H')):
            hr = int(re.search(r"(\d+)H", idleSecondsPT).group(1))
        if (idleSecondsPT.__contains__('M')):
            min = int(re.search(r"(\d+)M", idleSecondsPT).group(1))
        if (idleSecondsPT.__contains__('S')):
            sec = int(re.search(r"(\d+)S", idleSecondsPT).group(1))

        idleSeconds = hr*60*60 + min*60 + sec
        self.idleSeconds = idleSeconds
    
        return idleSeconds

    def releaseIdleNodes(self, computeName, idleSecondsPT):
        # idleNodeCount, idleSecondsPT = getComputeIdleNodesCount(computeName)
        if (self.__getComputeScaleDownIdleSeconds__(idleSecondsPT) > 1):
            compute_target = ComputeTarget(workspace=self.ws, name=computeName)

            compute_target.update(idle_seconds_before_scaledown=1)
            compute_target.wait_for_completion(show_output=True)
            time.sleep(2)

            compute_target.update(idle_seconds_before_scaledown=self.idleSeconds)
            compute_target.wait_for_completion(show_output=True)
        return True

# Test script
if __name__ == "__main__":
    exp_bucket = { "experiment1" : 32 ,
            "experiment1Internal" : (4*24), 
            "experiment2" : 4, 
            "experiment3" : 8, 
            "experiment4" : 4, 
            "experiment5" : 32, 
            "experiment6Internal" : (8*24),
            "experiment7" : 32,
            "experiment8" : 32
        }
    params = {
        "geography" : "US"
    }
    manager = InfraManager(params)
    exp_list = manager.manage(exp_bucket)
    