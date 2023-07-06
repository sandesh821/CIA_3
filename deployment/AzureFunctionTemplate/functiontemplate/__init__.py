#Copyright (c) Microsoft. All rights reserved.
import datetime
import logging
import os
import sys

import azure.functions as func

def main(mytimer: func.TimerRequest) -> None:
    dir_abs_path = os.getcwd()
    sys.path.insert(0, dir_abs_path)

    from func_$$updatedexperimentname$$.main import readConfig, getPredDate, getData

    utc_timestamp = datetime.datetime.utcnow().replace(
        tzinfo=datetime.timezone.utc).isoformat()

    logging.info('Python timer trigger function ran at %s', utc_timestamp)
    
    logging.info('Reading configurations')
    scoringConfig = readConfig()
    print(scoringConfig)
    logging.info(scoringConfig)

    modelName = scoringConfig.get("modelName")
    modelConfig = scoringConfig.get("parameters").get(modelName)
    try:
        #Read prediction date from configuration
        predDate = getPredDate(scoringConfig.get("experimentset"))

        logging.info('Reading data')
        data = getData(predDate)
        logging.info(data)

        scoringConfig["parameters"]["predDate"] = predDate

        logging.info('Generating predictions')
        # predict(scoringConfig)

        #Update prediction date from configuration
    except Exception as ex:
        logging.error(ex)
        logging.error("Prediction failed")
