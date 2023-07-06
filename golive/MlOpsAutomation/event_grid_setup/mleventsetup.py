#Copyright (c) Microsoft. All rights reserved.
# Importing Libraries
import json
import yaml
import os

# Reading Config
with open("./config.yaml", "r") as ymlfile:
    cfg = yaml.safe_load(ymlfile)

# Reading Template JSON
with open('./event_grid_setup/armtemplate.json','r') as armtemplate:
    template=json.load(armtemplate)

# Handlers
subscriptions = []
templist=[]

# Mapping Events and Functions
for func_idx in range(len(cfg["FunctionNames"])):
    for func_name in cfg["FunctionNames"][func_idx]:
        event_name = cfg['mleventsTypes'][func_idx]
        templist.append(f'{event_name}_{func_name}')
    subscriptions.append(templist)
    templist=[]

# Adding Subscriptions and Aligning Events
cfg['subscriptionNames'] = subscriptions
cfg["mleventsTypes"][0:5] = ["Microsoft.MachineLearningServices.ModelRegistered",
                  "Microsoft.MachineLearningServices.ModelDeployed",
                  "Microsoft.MachineLearningServices.RunCompleted",
                  "Microsoft.MachineLearningServices.RunStatusChanged",
                  "Microsoft.MachineLearningServices.DatasetDriftDetected"]


def systemtopic():
    '''
    Function to add System Topic.
    Args:
        None
    Returns:
        sys_topic::[list]
            System Topic Resource.

    '''
    # Adding System Topic from Config
    sys_topic = [
        {
            "type" : cfg["systemTopicType"],
            "name" : cfg["mlSystemTopicName"],
            "apiVersion" :cfg["apiVersion"],
            "location" : cfg["location"],
            "identity" : {"type": cfg["identity"]},
            "properties" : {
                "source": cfg["mlWorkspaceId"],
                "topicType" :cfg["mlTopicType"]
            }
        }
    ]

    return sys_topic


def subscription(cfg):
    '''
    Function to add Subscription.
    Args:
        None
    Returns:
        subs::[list]
            Event Subscription Resource.

    '''
    # Adding Event Subscription from Config
    subs= [
        {
            "type": cfg["subscriptionType"],
            "name" :cfg['mlSystemTopicName']+"/"+cfg['subscriptionNames'],
            "apiVersion": cfg["apiVersion"],
            "dependsOn": 
            [
                f"[resourceId('{cfg['systemTopicType']}','{cfg['mlSystemTopicName']}')]"
            ],
            "properties":{
                "destination":{
                    "properties":{
                        "resourceId": f"[concat('{cfg['functionAppResourceId']}', '/functions/{cfg['FunctionNames']}')]",
                        "maxEventPerBatch" : cfg["maxEventsPerBatch"],
                        "preferredBatchSizeInKilobytes" :cfg["preferredBatchSizeInKilobytes"]

                    },
                    "endpointType":cfg["endpointType"],
                    
                },
                "filter":{
                    "isSubjectCaseSensitive": "false",
                    "includedEventTypes":cfg["mleventsTypes"],
                    "subjectBeginsWith":"",
                    "subjectEndsWith":""
                },
                "labels" : [],
                "enableAdvancedFilteringOnArrays" : "true",
                "retryPolicy" : {
                    "maxDeliveryAttempts" : cfg["maxDeliveryAttempts"],
                    "eventTimeToLiveInMinutes" :cfg["eventTimeToLiveInMinutes"]
                }
            }
        }
    ]
    
    return subs


# Adding System Topic
template['resources'] = systemtopic()

# N x M Mapping
for i in range(len(cfg["mleventsTypes"])):
    tempcfg=cfg.copy()
    g="subscriptionNames"
    for subsnames,funcnames in zip (cfg[g][i],cfg['FunctionNames'][i]):
        tempcfg[g]=subsnames
        tempcfg["FunctionNames"]=funcnames
        tempcfg["mleventsTypes"]=[cfg["mleventsTypes"][i]]
              
        template['resources'].append(subscription(tempcfg)[0])

# Saving File
filename="mlworkspace.json"
path=os.path.join(cfg["templateSavePath"], filename)
with open(path,"w") as mlworskapce:
    json.dump(template,mlworskapce,indent=3) 