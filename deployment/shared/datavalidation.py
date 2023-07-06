#Copyright (c) Microsoft. All rights reserved.
import pandas as pd
import logging

from shared.dboperations import executeStoredProcedure

def is_not_empty(df):
    try:
        # return True if raw dataframe is not empty
        return len(df) != 0

    except Exception as error:
        logging.error("Error: %s" % error)
        return error

def check_unique_timestamp(df):
    try:
        # return True if raw dataframe contains only one timestamp 
        return len(df["TimeStamp"].unique()) == 1

    except Exception as error:
        logging.error("Error: %s" % error)
        return error

def check_pitag_count(df):
    try:
        # return True if raw dataframe contains same number of Pi_tag values as present in PiTag_v2 table in database. 
        # Return Equipment Clusert ID.
        Equipment_Cluster = df['EquipmentCluster'].unique()
        Equipment_Cluster_Id, PiTagCount = executeStoredProcedure("usp_getpitagcount","@equipmentcluster = ?", (Equipment_Cluster[0]),"dbo",1)
        
        return len(df["PiTag"].unique()) == PiTagCount, Equipment_Cluster_Id

    except Exception as error:
        logging.error("Error: %s" % error)
        return error
    
def contains_all_numeric_values(df):
    try:
        # return True if all rows in the value column of raw dataframe are numeric
        return pd.to_numeric(df['Value'], errors='coerce').notnull().all()

    except Exception as error:
        logging.error("Error: %s" % error)
        return error


#Testing validation Script
if __name__ == "__main__":
    # df = fetchData("RGTSU_JIT_PIValue_RealTime"," FileName ='pi-data/raw/2021/RGTEC_A_Compressor/RGTSUDX-RGTECACOMPRESSOR_ADLS2_20211222174900.json' ")
    d = {
        'unit': ['UD', 'UD', 'UD', 'UD', 'UD','UD'],
        'x': [ 'Q1', 'Q2', 'Q3', 'Q4','Q5','Q6'],
        'Value' : [ -1.48, 1.7, -6.18, 0.25, 'x', 0.25]
        }
        
    df = pd.DataFrame(d)
    print(df.head())

    print("Is File not Empty : %r" % is_not_empty(df))
    print("Is TimeStamp Unique : %r" % check_unique_timestamp(df))
    print("Does PiTag value matches with  PiTag_v2 table in DB : %r" % check_pitag_count(df)[0])
    print("Equipment Cluster ID : {}".format(check_pitag_count(df)[1]))

    
    print("Does File contains all non-numeric values : %r" % contains_all_numeric_values(df))
