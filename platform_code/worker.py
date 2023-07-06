#Copyright (c) Microsoft. All rights reserved.
import warnings
warnings.filterwarnings("ignore")
import subprocess
import pandas as pd
import numpy as np
import logging
import json
import os

from infrastructure_manager.InfraManager import InfraManager
from configyaml_generator.ExperimentConfigGenerator import ExperimentConfigGenerator
from masterConfiguration import mapproperty, configParams, azureDetails
from code.dboperations import dboperations
# from code.trainingPipeline import invokeTrainingPipeline


def startProcess():
    logging.info("Starting framework")

    infraParams = {}

    logging.info("Reading experiments list from database")
    # Get list of experiments to be scheduled
    experimentList = dboperations.executeStoredProcedure("usp_getExperimentsListForPipeline",None,None,"dbo",2)

    if len(experimentList) > 0:
        # Get Geography from database
        infraParams["geography"] = experimentList["GeographyName"].unique()[0]
        # Get horizon from database
        infraParams["horizon"] = experimentList["ForecastHorizon"].unique()[0]
        infraParams = {**infraParams, **azureDetails}

        # ===============Prepare Experiment List and update core requirements=====================
        # Scoring experiments
        if len(experimentList[experimentList["Status"]==3]) > 0:
            experimentList["scoringcores"] = experimentList[experimentList["Status"]==3].apply(mapproperty, axis=1,args=("scoringcores",1))
        else:
            experimentList["scoringcores"] = np.nan

        # Training experiments
        experimentList["coresNeeded"] = np.nan
        if len(experimentList[experimentList["Status"]==0]) > 0:
            experimentList["coresNeeded"] = experimentList[experimentList["Status"]==0].apply(mapproperty, axis=1,args=("cores",1))
        
        # Combine the fields
        experimentList["coresNeeded"] = experimentList["coresNeeded"].fillna(experimentList["scoringcores"])
        
        del experimentList["scoringcores"]
        print(experimentList)
        # ========================================================================================

        # ===============Initialize Infra manager=================
        logging.info("Scheduling "+ str(len(experimentList)) + " experiments")
        manager = InfraManager(infraParams)
        computeAllocationDF = manager.manage(experimentList)
        # ========================================================

        # ============Generate configurations using the specified computes================
        print(experimentList)
        configgenerator = configParams["configgenerator"]
        cg = ExperimentConfigGenerator(configgenerator,computeAllocationDF,experimentList)
        yamlFileList = cg.prepareConfigYAMLs()
        logging.info(yamlFileList)
        # ================================================================================

        # ==================Invoke training for the experiments allocated with computes=================

        for fileName in yamlFileList:
            status = experimentList[experimentList["experimenttag"] == fileName.replace(".yaml","")]["Status"]
            if status.values[0] == 0:
                logging.info("Triggering Pipeline for "+ str(fileName))
                strProcessCall = 'python code/trainingPipeline.py --configFile "'+os.getcwd()+"/"+configgenerator["outputPath"]+fileName+'"'
            elif status.values[0] == 3:
                logging.info("Triggering Scoring Pipeline for "+ str(fileName))
                strProcessCall = 'python code/scoringPipeline.py --configFile "'+os.getcwd()+"/"+configgenerator["outputPath"]+fileName+'"'
            # print(strProcessCall)
            subprocess.Popen(strProcessCall, shell=True)
        
        # ==============================================================================================
    else:
        logging.info("No experiments to schedule")
        
# Test Script
if __name__ == "__main__":
    startProcess()