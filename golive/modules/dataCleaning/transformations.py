#Copyright (c) Microsoft. All rights reserved.
# Import required modules
import warnings
warnings.filterwarnings("ignore")

import logging
from utilities.azure import blobOperations
from utilities.dboperations import dboperations
from workflow.common import getdata
from workflow.pages.transformations import getDF, performTransformations
from workflow.pages.mergefiles import performMergeOperations
from workflow.pages.featureengineering import performInterpolation, columnCreation
import pandas as pd
import goliveappconfig

def read_configurations(ExperimentSetID, fileConfiguration):
    # Get transformation file timezone details from database
    data = {"experimentsetid":goliveappconfig.experimentSetId}
    timezoneDataDetails = getdata.getTimezoneDetails(data)
    # Read data from database for merge configurations
    mergeDetails = getdata.getMergeSequence(data)
    mergeDetails = mergeDetails[0]
    
    df_dt = dboperations.executeStoredProcedure(goliveappconfig.GET_PREDICTION_SCHEDULE ,"@ExperimentSetID =?",(goliveappconfig.experimentSetId),goliveappconfig.goLiveSchema,1)
    date = pd.to_datetime(df_dt[0])

    experimentStore = {
        "experimentsetid": ExperimentSetID,
        "timezoneDataDetails": timezoneDataDetails,
        "fileConfiguration": fileConfiguration,
        "mergeConfigurations" : mergeDetails,
        "date": date
    }
    return experimentStore

def transformations(experimentStore):
    '''
    This function takes in a DataFrame, a source data dictionary, an experiment store, 
    and a list of time zone details, and performs time zone conversion on the data.
    
    Parameters:
    - experimentStore (dict): A dictionary containing information about the experiment.
    
    Returns:
    - tzdata (list): A list of dictionaries containing the time zone details for each file.
    - cleanedDF (pandas DataFrame): The input data with time zone conversion applied.
    '''
    fileConfiguration = experimentStore["fileConfiguration"]

    logging.info(fileConfiguration)
    
    mergeDetails = experimentStore["mergeConfigurations"]
    mergeFileIdentifiers = [mergeDetails["initFile"]]+eval(mergeDetails["fileIdentifiers"])
    listDF = [None]*len(mergeFileIdentifiers)
    print(mergeFileIdentifiers)
    for details in experimentStore["timezoneDataDetails"]:

        try: 
            # Extract FileType and FileIdentifierValue from i dictionary
            FileType = details['FileType']     
            FileIdentifierValue = details['FileIdentifier']
            idx = mergeFileIdentifiers.index(FileIdentifierValue)

            print(f"Processing data for {FileIdentifierValue}")
            filePath = fileConfiguration[FileIdentifierValue]

            # ===============Read the dataframe from blob===============
            _,df,_ = blobOperations.getBlobDf(goliveappconfig.sourceStorageAccount, goliveappconfig.sourceRawDataContainerName ,filePath)

            # ===============================TIMEZONE CONVERSION ===================================
            # Retrieve required details for available datetime
            selectAvailDatetimeDropdownStore = details["AvailColumnName"]
            checkAvailDatetimeTypeDropdownStore = details["AvailTZType"]
            availDatetimeConversionStore = details["AvailTZAware"]
            AvailTZConversionDropdownStore = details["AvailTZConversionUnit"]
            
            # Retrieve required details for application datetime
            selectDatetimeDropdownStore = details["DateTimeColumnName"]
            checkDatetimeTypeDropdownStore = details["DateTimeTZType"]
            dateTimeConversionStore = details["DateTimeTZAware"]
            TZConversionDropdownStore = details["DateTimeTZConversionUnit"]

            # Timezone conversion started
            if FileType != 'FutureCovariates' :
                cleanedDF = getDF(goliveappconfig.forecastTimezone,df,FileType,selectDatetimeDropdownStore ,checkDatetimeTypeDropdownStore,dateTimeConversionStore,TZConversionDropdownStore)
            else : 
                cleanedDF = getDF(goliveappconfig.forecastTimezone,df,FileType,selectDatetimeDropdownStore ,checkDatetimeTypeDropdownStore,dateTimeConversionStore,TZConversionDropdownStore,
                            selectAvailDatetimeDropdownStore,checkAvailDatetimeTypeDropdownStore,availDatetimeConversionStore,AvailTZConversionDropdownStore)
            #========================================================================
            # ======================Perform transformations =========================
            logging.info("Transforming "+ FileIdentifierValue)
            transformed_df = performTransformations(experimentStore,selectDatetimeDropdownStore,selectAvailDatetimeDropdownStore,FileIdentifierValue, FileType,cleanedDF,goliveappconfig.forecastGranularity)

            # Prepare listdf based on fileIdentifier order
            listDF[idx] = transformed_df

        except Exception as ex:
            logging.error(ex)
            logging.error("Error occured in transformation and merging operations")

    #==========================Perform Merge Operations =========================
    merged_df = performMergeOperations(mergeDetails["initFile"],eval(mergeDetails["operators"]),eval(mergeDetails["fileIdentifiers"]),goliveappconfig.forecastTimezone,"",listDF)
    
    #=========================Save cleaned df to blob========================
    fileName = "data_"+experimentStore["date"].strftime('%Y-%m-%d_%H%M%S')+".csv"
    targetFilePath = f"{goliveappconfig.filePathPrefix}/MergedCleanFiles/{fileName}"
    blobOperations.uploadDFToBlobStorage(merged_df,goliveappconfig.sourceStorageAccount, goliveappconfig.sourceCleanedDataContainerName,targetFilePath)
        
    # Create columns
    columnAddedDF,_  = columnCreation(experimentStore,merged_df)
    print(columnAddedDF)

    # Perform Interpolation
    interpolateTableDF = getdata.getInterpolationInfo(experimentStore)
    interpolateTableDF = pd.DataFrame(interpolateTableDF)
    if len(interpolateTableDF) < 1 :
        logging.error('Column Interpolation is not configured')
    final_df = performInterpolation(interpolateTableDF,columnAddedDF)

    #=========================Save cleaned df to blob========================
    targetFilePath = f"{goliveappconfig.filePathPrefix}/PreprocessedFiles/{fileName}"
    blobOperations.uploadDFToBlobStorage(final_df,goliveappconfig.sourceStorageAccount, goliveappconfig.sourceCleanedDataContainerName,targetFilePath)
    
    # Update status in db
    dboperations.executeStoredProcedure(goliveappconfig.UPDATE_PREDICTION_SCHEDULE ,"@ExperimentSetID =?,@PredictionDate=?,@DataCleaning=?",(goliveappconfig.experimentSetId,experimentStore["date"].strftime('%Y-%m-%d %H:%M:%S'),1),goliveappconfig.goLiveSchema,0)
    
    logging.info("Transformations completed")

        
def runCleaning(ExperimentSetID, fileConfiguration):

    experimentStore = read_configurations(ExperimentSetID, fileConfiguration)
    transformations(experimentStore)