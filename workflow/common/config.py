#Copyright (c) Microsoft. All rights reserved.
import os
ErrorAnalysisReport = os.environ.get("ErrorAnalysisReportURL")
DATA_SAVE_MESSAGE = "Data Saved Successfully proceed to next step"

# Landing page
GET_EXPERIMENT_SET_SP = 'usp_getExperimentSets'
SAVE_NEW_EXPERIMENT_SET_SP = 'usp_insertExperimentSets'

# Site Information page
GET_WIND_TURBINES_SP = "usp_getWindTurbines"
SAVE_SET_EXPERIMENT_DETAILS_SP = 'usp_insertExperimentSetDetails'
GET_EXPERIMENT_SET_DETAILS_SP = "usp_getExperimentSetDetails"

# Forecast setup page
SAVE_FORECAST_SETUP_DETAILS_SP = "usp_insertExperimentSetForecastSetupDetails"
GET_FORECAST_SETUP_DETAILS_SP = "usp_getExperimentSetForecastSetupDetails"
DELETE_FORECAST_SETUP_DETAILS_SP = "usp_deleteExperimentSetForecastSetupDetails"
GET_TIMEZONES_SP = "usp_getTimezones"

# Source data tab
SAVE_SOURCEDATA_DETAILS_SP = "usp_insertExperimentSetSourceDataDetails"
GET_SOURCEDATA_DETAILS_SP = "usp_getExperimentSetSourceDataDetails"
DELETE_SOURCEDATA_DETAILS_SP = "usp_deleteExperimentSetSourceDataDetails"

#Transformation Tab
SAVE_TIMEZONE_DETAILS_SP = "usp_insertTransformationFileTimezoneDetails"
DELETE_TIMEZONE_DETAILS_SP =  "usp_deleteTransformationFileTimezoneDetails"
GET_TIMEZONE_DETAILS_SP =  "usp_getTransformationFileTimezoneDetails"

SAVE_TRANSFORMATION_DETAILS_SP = "usp_insertTransformationDetails"
DELETE_TRANSFORMATION_DETAILS_SP =  "usp_deleteTransformationDetails"
GET_TRANSFORMATION_DETAILS_SP = "usp_getTransformationDetails"

SAVE_COLUMN_TRANSFORMATION_DETAILS_SP = "usp_insertColumnTransformationDetails"
DELETE_COLUMN_TRANSFORMATION_DETAILS_SP =  "usp_deleteColumnTransformationDetails"
GET_COLUMN_TRANSFORMATION_DETAILS_SP = "usp_getColumnTransformationDetails"

GET_COUNTRIES_DETAILS_SP = "usp_getCountries"

TIMEZONE_CLEANED_FOLDER = "TZCleanedFiles"
TRANSFORM_CLEANED_FOLDER = "TransformedFiles"
MERGED_FOLDER = "MergedFiles"
MASTER_FOLDER = "workflow"
MASTERCONTAINER = "workflowdata"
MergedFileName = 'MergedFile.csv'
PreprocessedFileName = 'PreprocessedFile.csv'

# NEWCOLUMNINFO SECTION

SAVE_NEWCOLUMNINFO_SP = "usp_insertNewColumnInfo"
DELETE_NEWCOLUMNINFO_SP =  "usp_deleteNewColumnInfo"
GET_NEWCOLUMNINFO_SP = "usp_getNewColumnInfo"

# INTERPOLATION SECTION

SAVE_INTERPOLATIONINFO_SP = "usp_insertInterpolationInfo"
DELETE_INTERPOLATIONINFO_SP =  "usp_deleteInterpolationInfo"
GET_INTERPOLATIONINFO_SP = "usp_getInterpolationInfo"

# Multivariate EDA SECTION

SAVE_MULTIVARIATEEDA_SP = "usp_insertMultivariateEDASelection"
DELETE_MULTIVARIATEEDA_SP =  "usp_deleteMultivariateEDASelection"
GET_MULTIVARIATEEDA_SP = "usp_getMultivariateEDASelection"

# ABALATION TAB
ALGORITHMS = ["DeepMC", "TFT", "DartsTCN", "DartsNBeats"] 
EXPERIMENTS_START_TAG = "experiment"

SAVE_EXPERIMENTS_LIST_SP = "usp_insertExperimentsList"
DELETE_EXPERIMENTS_LIST_SP =  "usp_deleteExperimentList"
GET_EXPERIMENTS_LIST_SP = "usp_getExperimentsList"

SCHEDULE_EXPERIMENTS_LIST_SP = "usp_scheduleExperimentsListForPipeline"
GET_ALL_EXPERIMENTS_SP = "usp_getAllScheduledExperimentsList"

GET_ALL_GEOGRAPHIES_SP = 'usp_getGeographies'
SAVE_GEOGRAPHY_INFO_SP = 'usp_saveSelectedGeography'

GET_ENTITYTYPE = "usp_getEntityType"

#Go-Live Configuration page
GET_TOP_MODELS_SP = "usp_getTopModels"
SAVE_MODEL_SELECTION_SP = "usp_insertModelDetails"
GET_MODEL_SELECTION_SP = "usp_getModelDetails"
DELETE_MODEL_SELECTION_SP = "usp_deleteModelDetails"

SAVE_DATA_INGESTION_SP = "usp_insertDataIngestion"
GET_DATA_INGESTION_SP = "usp_getDataIngestion"
DELETE_DATA_INGESTION_SP = "usp_deleteDataIngestion"

SAVE_EVENT_CONFIG_SP = "usp_insertEventConfiguration"
GET_EVENT_CONFIG_SP = "usp_getEventConfiguration"
DELETE_EVENT_CONFIG_SP = "usp_deleteEventConfiguration"

SAVE_MODEL_DEPLOYMENT_SP = "usp_insertModelDeployment"
GET_MODEL_DEPLOYMENT_SP = "usp_getModelDeployment"
DELETE_MODEL_DEPLOYMENT_SP = "usp_deleteModelDeployment"

SAVE_NOTIFICATION_CONFIG_SP = "usp_insertNotificationConfig"
GET_NOTIFICATION_CONFIG_SP = "usp_getNotificationConfig"
DELETE_NOTIFICATION_CONFIG_SP = "usp_deleteNotificationConfig"

# Provenance
pythonVersion = "3.8.5"

# Merge Page
DELETE_MERGEFILE_SP = "usp_deleteMergeFileSequence"
INSERT_MERGEFILE_SP = "usp_insertMergeSequence"
GET_MERGEFILE_SP = "usp_getMergeSequence"

frequencyOptions = [{'label' : 'Day', 'value' : 'D'} , {'label' : 'Hour', 'value' : 'H'} , {'label' : 'Minute', 'value' : 'min'}]
granularityOptions = [{'label' : 'Hour', 'value' : 'H'} , {'label' : 'Minute', 'value' : 'min'} ,{'label' : 'Seconds', 'value' : 'S'} ]
retrainFrequencyOptions = [{'label' : 'Day', 'value' : 'D'} , {'label' : 'Month', 'value' : 'M'}]
actionList = [{'label' : 'Retrain', 'value' : 'Retrain'}]
eventsList = [{'label' : 'Drift', 'value' : 'Drift'}]