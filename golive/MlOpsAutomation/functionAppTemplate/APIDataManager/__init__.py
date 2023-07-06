#Copyright (c) Microsoft. All rights reserved.
# Importing default utilities
import datetime
import logging
import azure.functions as func

# Importing module specific utilities
import requests
import pandas as pd
from utilities.azure import blobOperations
from utilities.dboperations import dboperations
from utilities.azure import keyvaultOperations
import goliveappconfig
from modules.apiManager import Solcast
from workflow.common import getdata
import time

def customizeSolcastAPIData(df: pd.DataFrame,dt):
    # TODO: To be moved to API Manager
    updated_df = df.rename(columns={"period_end": "DateTime", "cloud_opacity": "solcast_sol_cloud_opacity_fcst_dayahead", "ghi": "solcast_sol_ghi_fcst_dayahead"})
    updated_df["DateTime"] = pd.to_datetime(updated_df["DateTime"],utc=True).astype('datetime64[ns]').dt.tz_localize(None).dt.strftime('%Y-%m-%d %H:%M:%S')
    updated_df["AvailableTime"] = dt #(dt).strftime('%Y-%m-%d')+" "+goliveappconfig.forecastTime

    #TODO: limit the data as per forecast horizon
    print(len(updated_df))
    updated_df = updated_df[:(goliveappconfig.forecastHorizon+1)]

    return updated_df

def main(mytimer: func.TimerRequest) -> None:

    # # Check if Merge and Resampling completed for the prediction
    predictionFlowStatus = dboperations.executeStoredProcedure(goliveappconfig.GET_PREDICTION_SCHEDULE_STATUS ,"@ExperimentSetID =?",(goliveappconfig.experimentSetId),goliveappconfig.goLiveSchema,2)
    
    df_dt = dboperations.executeStoredProcedure(goliveappconfig.GET_PREDICTION_SCHEDULE ,"@ExperimentSetID =?",(goliveappconfig.experimentSetId),goliveappconfig.goLiveSchema,1)
    date = pd.to_datetime(df_dt[0])
    dt = date.strftime('%Y-%m-%d_%H%M%S')
    logging.info(date)
    
    if (predictionFlowStatus["APIDataRefresh"].values[0] is not None and int(predictionFlowStatus["APIDataRefresh"].values[0]) == 1):
        logging.info("API data refresh for latest prediction schedule already completed")
    else:
        # Get lat and long details
        siteDetails = getdata.getExperimentDetails({"experimentsetid":goliveappconfig.experimentSetId})

        apiList = goliveappconfig.api
        
        for key, value in apiList.items():

            cfg = {
                'api_name' : value,
                'api_call': goliveappconfig.api_call_type,
                'latitude': siteDetails["Lat"],
                'longitude': siteDetails["Long"],
                'output_parameters': goliveappconfig.output_parameters,
                'period': goliveappconfig.solcastForecastPeriod, # TODO: create a mapping between forecast frequency and api specific periods
                'start_date': (date).isoformat(), 
                'end_date': (date + datetime.timedelta(days=1)).isoformat()
            }
            solcast = Solcast.Solcast(cfg)
            solcastData = solcast.getData()
            logging.info(solcastData)

            if solcastData is not None:
                logging.info("Customizing api data to align with input")
                solcastData = customizeSolcastAPIData(solcastData,date)
                # Generate and upload blob
                blob = f"{goliveappconfig.filePathPrefix}/api/{key}_{dt}.csv"

                blobOperations.uploadDFToBlobStorage(solcastData,goliveappconfig.sourceStorageAccount,goliveappconfig.sourceRawDataContainerName, blob)
                # Update status in db

                logging.info("Updating database")
                dboperations.executeStoredProcedure(goliveappconfig.UPDATE_PREDICTION_SCHEDULE ,"@ExperimentSetID =?,@PredictionDate=?,@APIDataRefresh=?",(goliveappconfig.experimentSetId,df_dt[0],1),goliveappconfig.goLiveSchema,0)

            else:
                logging.info("No data received from API")

    while (True):
        # # Check if Merge and Resampling completed for the prediction
        predictionFlowStatus = dboperations.executeStoredProcedure(goliveappconfig.GET_PREDICTION_SCHEDULE_STATUS ,"@ExperimentSetID =?",(goliveappconfig.experimentSetId),goliveappconfig.goLiveSchema,2)
        
        if (predictionFlowStatus["MergedResampling"].values[0] is not None and int(predictionFlowStatus["MergedResampling"].values[0]) == 1):
            logging.info("Iot data merge and resampling completed")
            # If yes, trigger data cleaning
            # Set up the endpoint URL for your Azure Function
            secrets = keyvaultOperations.getSecrets(["functionAppMasterKey"])
            masterKey = secrets[0]
            endpoint_url = f"https://{goliveappconfig.functionAppName}.azurewebsites.net/api/preprocessdata/{dt}?code={masterKey}"
            logging.info(endpoint_url)
            # Make the request to the endpoint URL
            response = requests.get(endpoint_url)
            if response.status_code == 200:
                # Print the response from the function
                logging.info(response.text)
            else:
                logging.info("Data Merge trigger failed, HTTP response ")
                logging.info(response.status_code)
                logging.info(response.text)
            break
        else:
            time.sleep(5)