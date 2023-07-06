#Copyright (c) Microsoft. All rights reserved.

import pandas as pd
import pyodbc
import urllib
import logging
import time
import sys
import os

currentDir = os.path.dirname(os.path.abspath(os.path.join(__file__,"..")))
sys.path.insert(0,currentDir)

import dboperations.prepareConnection as connection
import dboperations.config as config

connectionString = connection.getConnectionString()
    
def executeStoredProcedure(procName,paramList,params,SchemaName = "dbo",isGetResult = 0):
    count = 0
    # Prepare sql connection with retry logic
    while count == 0 or count < config.cnxnRetryCount:
        try:
            cnxn = pyodbc.connect(connectionString)
            count = config.cnxnRetryCount
        except Exception as ex:
            count = count + 1
            time.sleep(15)

    cursor = cnxn.cursor()
    cnxn.autocommit = True
    # Prepare the stored procedure execution script and parameter values
    if params == None or paramList == None:
        storedProc = "Exec ["+SchemaName+"].["+procName+"] " 
        cursor.execute(storedProc)
    else:
        storedProc = "Exec ["+SchemaName+"].["+procName+"] " + paramList
        cursor.execute(storedProc, params)
    
    
    # Iterate the cursor
    if isGetResult == 1:
        row = cursor.fetchone() 
    elif isGetResult == 2:
        columns = [column[0] for column in cursor.description]
        row = cursor.fetchall() 
        for i in range(0,len(row)):
            row[i]=tuple(row[i])
        sql_data = pd.DataFrame(row, columns=columns)
    else:
        cursor.commit()
    # Close the cursor and delete it
    cursor.close()
    del cursor

    # Close the database connection
    cnxn.close()  
    if isGetResult == 1:
        return row
    elif isGetResult == 2:
        return sql_data
    else:    
        return "Data inserted successfully"

def insertDataFromDF(df, TableName, SchemaName = "dbo"):
    connectionString = prepareConnection.getConnectionString()
    count = 0
    # Prepare sql connection with retry logic
    while count == 0 or count < config.cnxnRetryCount:
        try:
            cnxn = pyodbc.connect(connectionString)
            count = config.cnxnRetryCount
        except Exception as ex:
            count = count + 1
            time.sleep(15)

    cursor = cnxn.cursor()
    cnxn.autocommit = True

    cols = ",".join([str(i) for i in df.columns.tolist()])
    try:
        for i,row in df.iterrows():
            sql = "INSERT INTO "+SchemaName+'.'+TableName+" (" +cols + ") VALUES (" + "?,"*(len(row)-1) + "?)" 
            cursor.execute(sql, *tuple(row))
    except Exception as ex:
        logging.error(ex)
        print(sql)
    # Close the cursor and delete it
    cursor.close()
    del cursor

    # Close the database connection
    cnxn.close()  

    return "Data inserted successfully"


# Test script
if __name__ == "__main__":
    data = executeStoredProcedure("usp_InsertRunTracking","@ExperimentSet=?, @Experiment = ?, @InternalRunID = ?, @AMLRunId = ?, @RunStatus = ?", ("c","e","w","z","a"),"logs",0)
    print(data)
    data = executeStoredProcedure("usp_InsertStatusTracker", "@AMLRunId = ?, @Status = ?,  @TotalEpoch = ?, @HPTPrecentageCompleted = ?, @InternalModelNumber = ?", ("9f4e5bb1-9cfd-43f9-ae5b-430c3cab9c64","training_hpt",10, 10.00, None),"logs",0)
    print(data)
