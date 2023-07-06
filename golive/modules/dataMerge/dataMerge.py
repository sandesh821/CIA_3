#Copyright (c) Microsoft. All rights reserved.
import pandas as pd
import logging
from utilities.azure import blobOperations

def mergeWithMaster(data,goliveappconfig):
    logging.info(data.columns)
    # Load master data file
    _,masterDF,_ = blobOperations.getBlobDf(goliveappconfig.sourceStorageAccount,goliveappconfig.sourceMasterDataContainerName,goliveappconfig.filePathPrefix+"/masterdata.csv")

    masterDF = masterDF[masterDF.columns.drop(list(masterDF.filter(regex='Unnamed')))]
    print(masterDF)
    masterDF.set_index(pd.DatetimeIndex(masterDF["DateTime"]),inplace=True)

    
    # Perform merge operation
    data = data[data.columns.drop(list(data.filter(regex='Unnamed')))]
    data.set_index(pd.DatetimeIndex(data["DateTime"]),inplace=True)
    print(data)

    # df3=masterDF.merge(data, how='outer', on = "DateTime")
    df3=masterDF.combine_first(data)
    logging.info(df3)

    blobOperations.uploadDFToBlobStorage(masterDF,goliveappconfig.sourceStorageAccount,goliveappconfig.sourceMasterDataContainerName,goliveappconfig.filePathPrefix+"/masterdata_old.csv",False)
    blobOperations.uploadDFToBlobStorage(df3,goliveappconfig.sourceStorageAccount,goliveappconfig.sourceMasterDataContainerName,goliveappconfig.filePathPrefix+"/masterdata.csv",False)
    
