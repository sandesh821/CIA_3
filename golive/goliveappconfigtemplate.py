#Copyright (c) Microsoft. All rights reserved.
import os
# Model details for which deployment is done
experimentSetId = '$$experimentSetId$$'
experimentSetName = "$$experimentSetName$$"
experimentTag = "$$experimentTag$$"
internalRunID = "$$internalRunID$$"
modelName = "$$modelName$$"
filePathPrefix = f"{experimentSetName}/{experimentTag}/{internalRunID}"

# Azure storage account and folder locations
sourceStreamingStorageAccount = "$$goliveStreamingStorageAccount$$"
sourceStreamingDataContainerName = "$$goliveStreamingDataContainer$$"

sourceStorageAccount = "$$goliveworkflowStorageAccount$$"
sourceRawDataContainerName = "rawdata"
sourceCleanedDataContainerName = "cleanedfiles"
sourceMergedDataContainerName = "mergedfiles"
sourceMasterDataContainerName = "masterdata"
sourceBadDataContainerName = "badfiles"
sourceProcessedDataContainerName = "processedfiles"
predictionContainerName = "predictions"

trainingSourceStorageAccount = "$$trainingSourceStorageAccount$$"
trainingSourceContainerName = "workflowdata"
trainingSourceDataPath = f"workflow/{experimentSetName}/MergedFiles/PreprocessedFile.csv"
scoringDataPath = f"scores/{filePathPrefix}/{modelName}/{modelName}_valResults.csv"

# Forecast configuration
forecastTime = "$$forecastTime$$"
forecastHorizon = '$$forecastHorizon$$'
forecastGranularity = "$$forecastGranularity$$"
forecastInitialwindow = "$$forecastInitialwindow$$"
lookback = '$$lookback$$'
forecastTimezone = "$$forecastTimezone$$"
api_call_type = "forecasts"
output_parameters = 'cloud_opacity,ghi'
solcastForecastPeriod = 'PT60M'
# FileIdentifiers
iotFileIdentifier = "$$iotFileIdentifier$$"
entityFileIdentifier = "$$entityFileIdentifier$$"
# API fileIdentifiers (fileIdentifier : API)
api = '$$apidata$$'

# Retraining history enabled
historyEnabled = '$$historyEnabled$$'

# Data drift rules
num_col_threshold = '$$num_col_threshold$$'
drift_share = '$$cat_col_threshold$$'
targetDriftColList =  ['Prediction']
pastCovariates =  '$$pastCovariates$$'
futureCovariates =  '$$futureCovariates$$'
colList = '$$colList$$'

# DB schema info
goLiveSchema = "golive"
workflowSchema = "dbo"

# DB Procedures
GET_TRANSFORMATIONS_SP = "usp_getTransformationDetails"

# golive SP
GET_PREDICTION_SCHEDULE = "usp_getPredictionSchedule"
GET_DATA_INGESTION = "usp_getDataIngestion"
UPDATE_PREDICTION_SCHEDULE = "usp_updatePredictionSchedule"
GET_PREDICTION_SCHEDULE_STATUS = "usp_getPredictionScheduleStatus"
ADD_MODEL_DRIFT_RESULT = "usp_InsertModelDriftAnalysisMetrics"
ADD_DATA_DRIFT_RESULT = "usp_InsertDataDriftAnalysisMetrics"
ADD_TARGET_DRIFT_RESULT = "usp_InsertTargetDriftAnalysisMetrics"

# Email Notification configurations
tolist = '$$tolist$$'
smtpServer = "$$smtpServer$$"
smtpPort = '$$smtpPort$$'
functionAppName = "$$functionAppName$$"