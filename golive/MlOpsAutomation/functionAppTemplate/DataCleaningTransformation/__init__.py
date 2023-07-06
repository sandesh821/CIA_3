#Copyright (c) Microsoft. All rights reserved.
import logging

import azure.functions as func

import os
import sys
parent_dir = os.path.abspath(os.path.join(os.getcwd(), '..')) 
sys.path.append(parent_dir)
from modules.dataCleaning import transformations
import goliveappconfig
from utilities.dboperations import dboperations

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    preddate = req.route_params.get('preddate')

    if preddate:
        # Utility Invocation
        fileConfigurations = {
            f"{goliveappconfig.iotFileIdentifier}" : f"{goliveappconfig.filePathPrefix}/intermediateMerge/{goliveappconfig.iotFileIdentifier}_{preddate}.csv",
            f"{goliveappconfig.entityFileIdentifier}" : f"{goliveappconfig.filePathPrefix}/intermediateMerge/{goliveappconfig.entityFileIdentifier}_{preddate}.csv"
        }
        for key , value in goliveappconfig.api.items():
            fileConfigurations[key] = f"{goliveappconfig.filePathPrefix}/api/{key}_{preddate}.csv"

        logging.info(fileConfigurations)
        transformations.runCleaning(goliveappconfig.experimentSetId,fileConfigurations)
        
        return func.HttpResponse(f"Transformation executed successfully.")
    else:
        return func.HttpResponse(
             "Transformation cannot be processed",
             status_code=200
        )
