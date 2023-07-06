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
from infrastructure_manager.binPacking import BinPacking
from infrastructure_manager.amlOperations import AMLOperations
from infrastructure_manager.linearSumAssignment import NodeManagement
import numpy as np
from masterConfiguration import DEEPMC_INTERNALMODELS_COMPUTESIZE

class InfraManager(AMLOperations):
    def __init__(self,params):
        super().__init__(params)
        self.horizon = params.get("horizon")  

    def __getBinnedList__(self,exp_bucket):
        # Get core quota, available capacity of vCores region wise
        self.__getCapacities__()
        exp_compute_list = BinPacking.packing2dOptimizer(exp_bucket, self.compute_bucket, self.location_bucket)
        
        dfBin = pd.DataFrame(exp_compute_list, columns=['location', 'pack_data'])
        binnedDF = pd.DataFrame(columns=["location","experimenttag","coresNeeded"])
        for index, row in dfBin.iterrows():
            df = pd.json_normalize(row.pack_data).transpose().reset_index()
            df.columns=["experimenttag","coresNeeded"]
            df["location"] = row["location"]
            if binnedDF.empty:
                binnedDF = df
            else:
                binnedDF = pd.concat([binnedDF,df])
        return binnedDF

    def __prepareExperimentBuckets__(self,experimentList):
        finalExperiments = {}
        self.experimentList = experimentList
        for i, row in experimentList.iterrows():
            finalExperiments[row["experimenttag"]] = row["coresNeeded"]
            if row["algorithm"] == "DeepMC" and row["Status"] == 0:
                finalExperiments[row["experimenttag"]+"Internal"] = (DEEPMC_INTERNALMODELS_COMPUTESIZE, self.horizon) #8 cores are needed for DeepMC internal pipeline

        return finalExperiments

    def manage(self,experimentList):
        
        exp_bucket = self.__prepareExperimentBuckets__(experimentList)

        # Get list of all compute clusters present in current workspace
        self.__getWorkspaceComputes__()
        self.locations = self.computes["location"].unique().tolist()
       
        experimentStatus = pd.DataFrame(columns=["experimenttag","Cores", "NodeCount"])
        for key in exp_bucket:
            if "internal" in key.lower():
                cores = exp_bucket[key][0]
                nodes = exp_bucket[key][1]
            else: 
                cores = exp_bucket[key]
                nodes = 1
            
            experimentStatus = experimentStatus.append({'experimenttag': key, 'Cores': cores, "NodeCount": nodes, "requestedCores": (int(cores)*int(nodes))}, ignore_index=True)

        print("List of Experiments to be scheduled: ")
        print(experimentStatus)

        experimentStatus["Compute"] = np.NaN
        experimentStatus["location"] = np.NaN
        experimentStatus["AssignedStatus"] = False

        print("Experiment not supported: ")
        # Validate if the compute of the requested size is not available skip the experiment
        experimentStatus = experimentStatus[(experimentStatus['Cores'].isin(self.computes["numberOfCores"]))]

        print("Experiments to be processed: ")
        print(experimentStatus)

        # ==================Allocate compute by idle nodes=======================
        nodeBin = self.computes[self.computes["idleNodeCount"] != 0] 

        if (len(nodeBin)):
            nodeBin.reset_index(inplace=True)
            bins = []
            for i, row in nodeBin.iterrows():
                bins = bins + ([(row["location"], row["numberOfCores"], row["name"], row["nodeIdleTimeBeforeScaleDown"])]* row["idleNodeCount"])
            jobs = list(experimentStatus["requestedCores"].values)
            nd = NodeManagement()
            assigned_node_inds, assigned_job_inds, to_be_killed_node_ids = nd.apply_matching(jobs, bins)
            for i in range(len(assigned_job_inds)):
                idx = assigned_job_inds[i]
                # Change the status of jobs assigned with idle node
                experimentStatus.at[idx, "AssignedStatus"] = True
                assignedNode = bins[assigned_node_inds[i]]
                assignedNodeLocation = assignedNode[0]
                experimentStatus["location"] = experimentStatus["location"].astype(str)
                experimentStatus.at[idx, "location"] = assignedNodeLocation
                experimentStatus["Compute"] = experimentStatus["Compute"].astype(str)
                experimentStatus.at[idx, "Compute"] = nodeBin["name"][nodeBin["numberOfCores"] == assignedNode[1]].values[0]
            print("=====================After idle node assignment===========")
            
            #TODO:
            # Create objects for Compute, Experiment
            
            # Delete the idle nodes which are not needed as per the current requirement
            if (len(to_be_killed_node_ids) > 0):
                for i in to_be_killed_node_ids:
                    self.releaseIdleNodes(bins[i][2], bins[i][3])
            
        #===================Allocate cores for the experiments pending in pipeline====================
        # Prepare list of pending experiments
        pendingExperiments = experimentStatus[experimentStatus["AssignedStatus"]==False].reset_index(drop=True)
        pendingExperimentsDict = dict(pendingExperiments[['experimenttag','requestedCores']].values)
        dfBin = self.__getBinnedList__(pendingExperimentsDict)
        # Get the cores for each experiment
        dfBin = dfBin.merge(pendingExperiments[["experimenttag","Cores"]],left_on=["experimenttag"],right_on=["experimenttag"],how="inner")

        # Get cluster name for each experiment as per the assignment in regions after binning
        binnedWithCluster = dfBin.merge(self.computes,left_on=["location","Cores"], right_on=["location","numberOfCores"],how="inner",suffixes=('', '_right'))
        binnedWithCluster.rename(columns={"name":"Compute"},inplace=True)
        binnedWithCluster = binnedWithCluster[['experimenttag', 'coresNeeded', 'location', 'Compute', 'vmSize', 'numberOfCores']]
        binnedWithCluster = binnedWithCluster.groupby('experimenttag').first()
        experimentStatus.set_index("experimenttag", inplace=True, drop=True)
        experimentStatus.update(binnedWithCluster, join="left", overwrite=True)
        experimentStatus.loc[experimentStatus["Compute"].isna() == False, "AssignedStatus"] = True

        experimentStatus = experimentStatus[["Compute"]].dropna()

        
        # experimentStatus = experimentStatus.merge(self.experimentList[["experimenttag","algorithm"]],left_on=["experimenttag"], right_on=["experimenttag"],how="left",suffixes=('', '_right'))

        print("Allocation list: ")
        print(experimentStatus)
        return experimentStatus

# Test script
if __name__ == "__main__":
    # TODO: 
    # 1. Enhance to use classes for Compute and Experiment
    # 2. Support for GPU
    
    exp_bucket = { "experiment1" : 32 ,
            "experiment1Internal" : (4,24), 
            "experiment2" : 4, 
            "experiment3" : 8, 
            "experiment4" : 4, 
            "experiment5" : 32, 
            "experiment6Internal" : (8,24),
            "experiment7" : 32,
            "experiment8" : 4,
            "experiment6" : 64
        }
    params = {
        "geography" : "US"
    } 
    manager = InfraManager(params)
    exp_list = manager.manage(exp_bucket)