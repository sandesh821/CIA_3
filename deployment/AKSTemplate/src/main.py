import warnings
warnings.filterwarnings("ignore", category=UserWarning)

import os
import sys
import inspect

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir) 

from src.code.mlcode.$$scorescript$$ import init,run
from src.readBlob import loadDataFromBlob, saveDFToBlob
from src.code.mlcode.dboperations import dboperations
from src.utilities.emailNotification import sendmail
import pandas as pd
import logging
import yaml
import ast
import logging
import json

#===================Load configurations===================
try:
    with open("./scoringconfig.yaml", 'r') as file:
        confg = yaml.safe_load(file)
except (IOError, ValueError, EOFError, FileNotFoundError) as ex:
    logging.error("Config file not found")
    logging.error(ex)
    raise ex
except Exception as YAMLFormatException:
    logging.error("Config file not found")
    logging.error(YAMLFormatException)
    raise YAMLFormatException
scoring_config = str(confg.get('ScoringConfig',{}))
scoring_config_parsed = ast.literal_eval(scoring_config)

sourcestorage = "$$storageaccount$$"
sourcecontainer = "$$containername$$"
experimentsetid = $$experimentsetid$$
GET_PREDICTION_SCHEDULE = "usp_getPredictionSchedule"
UPDATE_PREDICTION_SCHEDULE = "usp_updatePredictionSchedule"
GET_PREDICTION_SCHEDULE_STATUS = "usp_getPredictionScheduleStatus"

def loadData():
    global scoring_config_parsed, pred_date
    print(scoring_config_parsed["modelPath"].replace("outputs/",""))
    logging.info(sourcestorage)
    logging.info(sourcecontainer)
    logging.info(scoring_config_parsed["modelPath"].replace("outputs/",""))
    # Load data from master file
    inputData = loadDataFromBlob(sourcestorage,sourcecontainer,scoring_config_parsed["modelPath"].replace("outputs/","")+"masterdata.csv")
    # Temporary

    # Get prediction data from database
    df_dt = dboperations.executeStoredProcedure(GET_PREDICTION_SCHEDULE ,"@ExperimentSetID =?",(experimentsetid),"golive",1)
    date = pd.to_datetime(df_dt[0])
    pred_date = df_dt[0]

    # Update the prediction date in config
    parameters = scoring_config_parsed["parameters"]
    modelParams = parameters[scoring_config_parsed["modelName"]]
    modelParams["predDate"] = date
    scoring_config_parsed["parameters"]["modelName"] = modelParams

    if scoring_config_parsed["modelName"] == "DeepMC":
        previousPoints = modelParams["trunc"]
        futurePoints = modelParams["horizon"]
    else:
        previousPoints = modelParams["lookback"]
        futurePoints = modelParams["forecast_horizon"]

    startIndex = len(inputData[inputData.index<date])-previousPoints 
    score_input = inputData[startIndex:]
    endIndex = len(score_input[score_input.index<date])+futurePoints
    score_input = score_input[:endIndex]
    score_input["DateTime"] = score_input.index
    # Fill empty records with 0
    score_input = score_input.fillna(0.0)

    print(scoring_config_parsed)

    return score_input

def main():
    global scoring_config_parsed
    logging.info("Main function loaded")
    predStatus = dboperations.executeStoredProcedure(GET_PREDICTION_SCHEDULE_STATUS ,"@ExperimentSetID =?",(experimentsetid),"golive",2)
    predStatus = predStatus.to_dict("records")[0]
    print(predStatus)
    
    if predStatus["DataDriftValidation"] == 1:
        try:
            data = loadData()
            logging.info(len(data))
        except Exception as ex:
            logging.error(ex)
            print("Error in reading input data")
            logging.info("Error in reading input data")
            raise ex

        if len(data) != 0:
            print("Start: Initializing model")
            init(scoring_config_parsed)
            print("End: Initializing model")

            print("Start: Prediction from model")
            try: 
                pred_result = run(data)
                print("End: Prediction from model")

                print("Start: Save predictions")
                saveDFToBlob(sourcestorage,"predictions",pred_result,scoring_config_parsed["modelPath"].replace("outputs/","")+"predictions_"+pd.to_datetime(pred_date).strftime('%Y-%m-%d_%H%M%S')+".csv")
                print("End: Save predictions")

                print("Start: Update schedule")
                dboperations.executeStoredProcedure(UPDATE_PREDICTION_SCHEDULE ,"@ExperimentSetID =?, @PredictionDate=?",(experimentsetid, pred_date),"golive",0)
                print("End: Update schedule")
                # sendmail.EmailNotification(f'Notification: {scoring_config_parsed["experimentSetName"]} predcitons generated',f'Predictions are generated for {pred_date} and are available in blob storage',goliveappconfig.tolist)
            except:
                print("Prediction failed")
                # sendmail.EmailNotification(f'Alert: Prediction failed for {scoring_config_parsed["experimentSetName"]}',f'Predictions generation failed for {pred_date}',goliveappconfig.tolist)
        else:
            print("Drift detected prediction skipped")
            # sendmail.EmailNotification(f'Alert: Prediction failed for {scoring_config_parsed["experimentSetName"]}',f'Input dataset is Empty for {pred_date}',goliveappconfig.tolist)
    else:
        print("Drift detected prediction skipped")
        # sendmail.EmailNotification('Alert: Data drift detected',f'Data drift validation failed for {pred_date}',goliveappconfig.tolist)

    if (predStatus["ModelDriftValidation"] == 0):
        print("Predictions generated with Target drift")
        # sendmail.EmailNotification('Notification: {scoring_config_parsed["experimentSetName"]} predcitons generated',f'Predictions are generated for {pred_date} and are available in blob storage with target data drift',goliveappconfig.tolist)

    return "Success"

main()