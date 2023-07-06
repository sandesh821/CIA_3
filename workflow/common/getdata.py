#Copyright (c) Microsoft. All rights reserved.
import json
from utilities.dboperations import dboperations
from workflow.common.config import *

# Return data in json format
def getJSONData(spname,data,schema="dbo"):
    try:
        df = dboperations.executeStoredProcedure(spname,"@ExperimentSetID =?",(data["experimentsetid"]),schema,1)
        df = json.loads(df[0])
        return df
    except Exception as ex:
        print(ex)
        return None

# Return data in pandas dataframe format
def getDFData(spname,data,schema="dbo"):
    df = dboperations.executeStoredProcedure(spname,"@ExperimentSetID =?",(data["experimentsetid"]),schema,2)
    return df

# Return data in dictionary format
def getDFToDictData(spname,data,schema="dbo"):
    try:
        df = dboperations.executeStoredProcedure(spname ,"@ExperimentSetID =?",(data["experimentsetid"]),schema,2)
        return df.to_dict("records")
    except:
        return None

# Get experiment details from data for the selected experiment set id
def getExperimentDetails(data):
    return getJSONData(GET_EXPERIMENT_SET_DETAILS_SP,data)

# Get experiment details from data for the selected experiment set id
def getForecastSetupDetails(data):
    return getDFData(GET_FORECAST_SETUP_DETAILS_SP,data)

# Get experiment details from data for the selected experiment set id
def getSourceDataDetails(data):
    return getDFData(GET_SOURCEDATA_DETAILS_SP,data)

# Get Countries List
def getCountries():
    data = dboperations.executeStoredProcedure(GET_COUNTRIES_DETAILS_SP ,None,None,"dbo",2)
    return data
# Get experiment details from data for the selected experiment set id
def getTransformationDetails(data):
    return getDFToDictData(GET_TRANSFORMATION_DETAILS_SP,data)

# Get experiment details from data for the selected experiment set id
def getColumnTransformationDetails(data):
    return getDFToDictData(GET_COLUMN_TRANSFORMATION_DETAILS_SP,data)

# Get experiment details from data for the selected experiment set id
def getTimezoneDetails(data):
    return getJSONData(GET_TIMEZONE_DETAILS_SP,data)

# Get experiment details from data for the selected experiment set id
def getMergeSequence(data):
    return getDFToDictData(GET_MERGEFILE_SP,data)

# Get new column information from data for the selected experiment set id
def getNewColumnInfo(data):
    return getJSONData(GET_NEWCOLUMNINFO_SP,data)

# Get new column information from data for the selected experiment set id
def getInterpolationInfo(data):
    return getJSONData(GET_INTERPOLATIONINFO_SP,data)

# Get new column information from data for the selected experiment set id
def getMultiVariateEDASelections(data):
    return getJSONData(GET_MULTIVARIATEEDA_SP,data)

# Get list of experiments and metadata for Provenance page
def getAllScheduledExperiments(data):
    return getDFToDictData(GET_ALL_EXPERIMENTS_SP,data)

# Get experiment details from data for the selected experiment set id
def getGeographyData():
    df = dboperations.executeStoredProcedure(GET_ALL_GEOGRAPHIES_SP,None,None,"dbo",2)
    return df["GeographyName"].to_list()

# Get list of experiments and metadata for Provenance page
def getSavedExperiments(data):
    return getDFToDictData(GET_EXPERIMENTS_LIST_SP,data)

# Return data in pandas dataframe format
def getEntityType(data):
    return getDFToDictData(GET_ENTITYTYPE,data)

# GO LIVE PAGE data methods

def getModelDetails(data, type):
    modelDetails = dboperations.executeStoredProcedure(GET_MODEL_SELECTION_SP,"@ExperimentSetID =?",(data["experimentsetid"]),"golive",1)
    modelDetails = json.loads(modelDetails[0])
    selectedModel = modelDetails[type+"_model"]
    return selectedModel

def getDataIngestionDetails(data):
    dataIngestionDF = dboperations.executeStoredProcedure(GET_DATA_INGESTION_SP,"@ExperimentSetID =?",(data["experimentsetid"]),"golive",2)
    return dataIngestionDF

def getEventConfigurationDetails(data):
    df = getJSONData(GET_EVENT_CONFIG_SP,data,"golive")
    return df

# Return data in pandas dataframe format
def getModelDeploymentConfigurations(data,schema):
    return getDFToDictData(GET_MODEL_DEPLOYMENT_SP,data,schema)

def getNotificationConfigurations(data):
    dict =  getDFToDictData(GET_NOTIFICATION_CONFIG_SP,data,"golive")
    return json.loads(dict[0]["notificationConfig"])
