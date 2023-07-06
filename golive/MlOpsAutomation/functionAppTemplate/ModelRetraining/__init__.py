#Copyright (c) Microsoft. All rights reserved.
import logging
import pandas as pd
import azure.functions as func

from modules.retraining import retraining
from utilities.azure import blobOperations
from utilities.dboperations import dboperations
import goliveappconfig

def main(mytimer: func.TimerRequest) -> None:
    logging.info("Retraining started")
    retraining.scheduleRetrainingExperiment(goliveappconfig)

    
