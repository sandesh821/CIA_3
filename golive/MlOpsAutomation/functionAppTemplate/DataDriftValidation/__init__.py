#Copyright (c) Microsoft. All rights reserved.
# Importing default utilities
import logging
import json
import pandas as pd
import azure.functions as func
import requests
# Importing additional utilities
from modules.driftValidation import dataDriftValidation, targetDriftValidation
from modules.dataMerge import dataMerge
import goliveappconfig
from utilities.dboperations import dboperations
from utilities.azure import keyvaultOperations
from utilities.emailNotification import sendmail
from utilities.azure import devops
from utilities import config

def main(myblob: func.InputStream):
    logging.info(myblob.name)
    
    if "PreprocessedFiles" in myblob.name:
        df_dt = dboperations.executeStoredProcedure(goliveappconfig.GET_PREDICTION_SCHEDULE ,"@ExperimentSetID =?",(goliveappconfig.experimentSetId),goliveappconfig.goLiveSchema,1)
        date = pd.to_datetime(df_dt[0])

        fileName = myblob.name.replace(goliveappconfig.sourceCleanedDataContainerName+"/","")

        # Checking for DataDrift
        cfg = {
                'storage_acc_name': goliveappconfig.sourceStorageAccount,
                'container_name': goliveappconfig.sourceCleanedDataContainerName,
                'input_file_name': fileName,
                'source_storage_acc_name': goliveappconfig.sourceStorageAccount,
                'source_container_name': goliveappconfig.sourceMasterDataContainerName,
                'training_file_name': goliveappconfig.filePathPrefix+"/masterdata.csv",
                'num_col_threshold' : goliveappconfig.num_col_threshold,
                'drift_share': goliveappconfig.drift_share,
                'targetDriftColList': goliveappconfig.targetDriftColList,
                "pastCovariates": goliveappconfig.pastCovariates,
                "futureCovariates": goliveappconfig.futureCovariates,
                "lookback" : goliveappconfig.lookback,
                "lookahead" : goliveappconfig.forecastHorizon
        }
        try:
            dataDrift = dataDriftValidation.DataDrift(config = cfg)
            driftResults, dataset_drift = dataDrift.get_df_drifts()
            logging.info(driftResults)
            logging.info(dataset_drift)

            dboperations.executeStoredProcedure(procName=goliveappconfig.ADD_DATA_DRIFT_RESULT, paramList='@ExperimentSetId=?, @DataDrift = ?', params=(goliveappconfig.experimentSetId ,json.dumps(driftResults)), SchemaName=goliveappconfig.goLiveSchema, isGetResult=0)
            
            if dataset_drift:
                logging.info("Data drift validation failed")
                
                # Send notification if drift detected and add status as data drift detected in prediction schedule
                sendmail.EmailNotification('Alert: Data Drift detected','Data drift validation failed',goliveappconfig.tolist,goliveappconfig.smtpServer,goliveappconfig.smtpPort)

                # Update status in db to 0 as failed status
                dboperations.executeStoredProcedure(goliveappconfig.UPDATE_PREDICTION_SCHEDULE ,"@ExperimentSetID =?,@PredictionDate=?,@DataDriftValidation=?",(goliveappconfig.experimentSetId,df_dt[0],0),goliveappconfig.goLiveSchema,0)
            else:
                # Update status in db to 1 as success status
                dboperations.executeStoredProcedure(goliveappconfig.UPDATE_PREDICTION_SCHEDULE ,"@ExperimentSetID =?,@PredictionDate=?,@DataDriftValidation=?",(goliveappconfig.experimentSetId,df_dt[0],1),goliveappconfig.goLiveSchema,0)
                
                # Performing data merge with the master data if there is no data drift
                logging.info("Merging with master data")
                mergedData = pd.read_csv(myblob)
                dataMerge.mergeWithMaster(mergedData,goliveappconfig)

                try:
                    # Pick the scoring as the source training file
                    # Identify prediction file for previous schedule
                    predictionFlowStatus = dboperations.executeStoredProcedure(goliveappconfig.GET_PREDICTION_SCHEDULE_STATUS ,"@ExperimentSetID =?",(goliveappconfig.experimentSetId),goliveappconfig.goLiveSchema,2)

                    if predictionFlowStatus["PreviousPredictionDate"].values[0] is not None:
                        logging.info(pd.to_datetime(predictionFlowStatus["PreviousPredictionDate"].values[0]).strftime('%Y-%m-%d_%H%M%S'))
                        cfg["training_file_name"] = goliveappconfig.filePathPrefix+"/batchscoring.csv"
                        cfg["input_file_name"] = goliveappconfig.filePathPrefix+"/predictions_"+pd.to_datetime(predictionFlowStatus["PreviousPredictionDate"].values[0]).strftime('%Y-%m-%d_%H%M%S')+".csv"
                        cfg["container_name"] = goliveappconfig.predictionContainerName
                        # Proceed to perform target drift validation
                        logging.info("Perform Target drift")
                        tgtDrift= targetDriftValidation.TargetDrift(config = cfg)
                        tgtDrifts = tgtDrift.get_df_drifts()

                        # If target drift detected, Update in database
                        if tgtDrifts["drift_detected"] == True:
                            # Send notification if drift detected and add status as data drift detected in prediction schedule
                            sendmail.EmailNotification('Alert: Target Drift detected','Target drift validation failed',goliveappconfig.tolist,goliveappconfig.smtpServer,goliveappconfig.smtpPort)
                            # Update status in db to 0 as failed status
                            dboperations.executeStoredProcedure(goliveappconfig.UPDATE_PREDICTION_SCHEDULE ,"@ExperimentSetID =?,@PredictionDate=?,@ModelDriftValidation=?",(goliveappconfig.experimentSetId,df_dt[0],0),goliveappconfig.goLiveSchema,0)

                            # =======Trigger alternate model dpeloyment=======
                            # try:
                            #     data = {
                            #         "experimentsetid":goliveappconfig.experimentSetId,
                            #         "experimentsetname" : goliveappconfig.experimentSetName,
                            #         "fileUpload" : "false",
                            #         "deploymentType" : "alternate"
                            #     }
                            #     devops.generateDevOpsRequest(config.GoLiveAppDeployemntBuildId,data)
                            #     devops.generateDevOpsRequest(config.DeploymentManagerBuildId,data)
                            # except Exception as ex:
                            #     logging.error(ex)
                            #     logging.error("Deployment requests failed, please check connection to devops")
                            # =========Retraining for the current model========
                            try:
                                # Get master key from keyvault
                                secrets = keyvaultOperations.getSecrets(["functionAppMasterKey"])
                                masterKey = secrets[0]
                                headers = {"x-functions-key": masterKey,"content-type": "application/json"}
                                endpoint_url = f"https://{goliveappconfig.functionAppName}.azurewebsites.net/admin/functions/ModelRetraining/"
                    
                                # Make the request to the endpoint URL
                                response = requests.post(endpoint_url, headers= headers, data="{}")
                                if response.status_code == 202:
                                    # Print the response from the function
                                    logging.info(response.text)
                                    logging.info("Retraining request submitted")
                                else:
                                    logging.info("Retraining trigger failed, HTTP response ")
                                    logging.info(response.status_code)
                                    logging.info(response.text)
                            except Exception as ex:
                                logging.error(ex)
                                logging.error("Retraining request failed")

                            # TODO: Set the status in database as current selected model is alternate model
                        else:
                            logging.info(" No predictions found for last prediction date, skipping target drift detection")
                            dboperations.executeStoredProcedure(goliveappconfig.UPDATE_PREDICTION_SCHEDULE ,"@ExperimentSetID =?,@PredictionDate=?,@ModelDriftValidation=?",(goliveappconfig.experimentSetId,df_dt[0],1),goliveappconfig.goLiveSchema,0)
                    else:
                        # Update status in db to 1 as success status
                        dboperations.executeStoredProcedure(goliveappconfig.UPDATE_PREDICTION_SCHEDULE ,"@ExperimentSetID =?,@PredictionDate=?,@ModelDriftValidation=?",(goliveappconfig.experimentSetId,df_dt[0],1),goliveappconfig.goLiveSchema,0)
                except Exception as ex:
                        logging.info(ex)
                        # Update status in db to 0 as failed status
                        dboperations.executeStoredProcedure(goliveappconfig.UPDATE_PREDICTION_SCHEDULE ,"@ExperimentSetID =?,@PredictionDate=?,@ModelDriftValidation=?",(goliveappconfig.experimentSetId,df_dt[0],0),goliveappconfig.goLiveSchema,0)
        except Exception as ex:
            logging.error(ex)
            dboperations.executeStoredProcedure(goliveappconfig.UPDATE_PREDICTION_SCHEDULE ,"@ExperimentSetID =?,@PredictionDate=?,@DataDriftValidation=?",(goliveappconfig.experimentSetId,df_dt[0],0),goliveappconfig.goLiveSchema,0)