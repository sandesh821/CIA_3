#Copyright (c) Microsoft. All rights reserved.
# Importing Libraries
import json
import yaml
import os

# Reading Config
with open("./config.yaml", "r") as ymlfile:
    cfg = yaml.full_load(ymlfile)

# Reading Template JSON
with open('./event_grid_setup/armtemplate.json','r') as armtemplate:
    template=json.load(armtemplate)

# Handlers
subscriptions = []
templist=[]

# Mapping Events and Functions
for func_idx in range(len(cfg["FunctionNames"])):
    for func_name in cfg["FunctionNames"][func_idx]:
        event = cfg['storageEventTypes'][func_idx]
        templist.append(f'{event}_{func_name}')
    subscriptions.append(templist)
    templist=[]

# Adding Subscriptions and Aligning Events
cfg['subscriptionNames'] = subscriptions
cfg["storageEventTypes"][0:5]=["Microsoft.Storage.BlobCreated",
                    "Microsoft.Storage.BlobDeleted",
                    "Microsoft.Storage.DirectoryCreated",
                    "Microsoft.Storage.DirectoryDeleted",
                    "Microsoft.Storage.BlobRenamed"]


def storageSystemTopic():
    '''
    Function to add System Topic.
    Args:
        None
    Returns:
        systemTopic::[list]
            System Topic Resource.

    '''
    # Adding System Topic from Config
    systemTopic=[
        {
            "type" : cfg["systemTopicType"],
            "name" : cfg["systemTopicName"],
            "apiVersion" :cfg["apiVersion"],
            "location" : cfg["location"],
            "identity" : {"type": cfg["identity"]},
            "properties" : {
                "source": f"[resourceId('{cfg['sourceTopicType']}','{cfg['blobName']}')]",
                "topicType" :cfg["topicType"]
            }
        }
    ]

    return systemTopic


def storageSubscription(cfg):
    '''
    Function to add Subscription.
    Args:
        None
    Returns:
        subscription::[list]
            Event Subscription Resource.

    '''
    # Adding Event Subscription from Config
    subscription=[
        {
            "type": cfg["subscriptionType"],
            "name" :cfg["systemTopicName"] + "/"+str(cfg["subscriptionNames"]),
            "apiVersion": cfg["apiVersion"],
            "dependsOn": 
            [
                f"[resourceId('{cfg['systemTopicType']}','{cfg['systemTopicName']}')]"
            ],
            "properties":{
                "destination":{
                    "properties":
                    {
                        "resourceId": f"[concat('{cfg['functionAppResourceId']}', '/functions/{cfg['FunctionNames']}')]",
                        "maxEventPerBatch" : cfg["maxEventsPerBatch"],
                        "preferredBatchSizeInKilobytes" :cfg["preferredBatchSizeInKilobytes"]

                    },
                    "endpointType":cfg["endpointType"],
                    
                },
                "filter":{
                    "isSubjectCaseSensitive": "false",
                    "includedEventTypes":cfg["storageEventTypes"],
                    "subjectBeginsWith":"",
                    "subjectEndsWith":""
                },
                "labels" : [],
                "enableAdvancedFilteringOnArrays" : "true",
                "retryPolicy" :{
                    "maxDeliveryAttempts" : cfg["maxDeliveryAttempts"],
                    "eventTimeToLiveInMinutes" :cfg["eventTimeToLiveInMinutes"]
                }
            }
        }
    ]

    return subscription

# Adding System Topic
template['resources'] = storageSystemTopic()

# N x M Mapping
for i in range(len(cfg["storageEventTypes"])):
    tempcfg=cfg.copy()
    g="subscriptionNames"
    for subsnames,funcnames in zip (cfg[g][i],cfg['FunctionNames'][i]):
        tempcfg[g]=subsnames
        tempcfg["FunctionNames"]=funcnames
        tempcfg["storageEventTypes"]=[cfg["storageEventTypes"][i]]
              
        template['resources'].append(storageSubscription(tempcfg)[0])

# Saving File
filename="storageaccount.json"
path=os.path.join(cfg["templateSavePath"], filename)
with open(path,"w") as mlworskapce:
    json.dump(template,mlworskapce,indent=3) 

