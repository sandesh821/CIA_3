#Copyright (c) Microsoft. All rights reserved.

import pandas as pd
import pyodbc
from utilities.dboperations import prepareConnection
import logging
import time
import utilities.config as config

def executeStoredProcedure(procName,paramList,params,SchemaName = "dbo",isGetResult = 0):
    connectionString = prepareConnection.getConnectionString()
    count = 0
    cnxn = None
    # Prepare sql connection with retry logic
    while count == 0 or count < config.cnxnRetryCount:
        try:
            cnxn = pyodbc.connect(connectionString)
            count = config.cnxnRetryCount
        except Exception as ex:
            logging.info("Database connection failed")
            logging.error(ex)
            print("Retry count: ", count)
            count = count + 1
            time.sleep(15)
    
    if cnxn is not None:
        cursor = cnxn.cursor()
        cnxn.autocommit = True
    
        try:
            #Prepare the stored procedure execution script and parameter values
            if params == None or paramList == None:
                storedProc = "Exec ["+SchemaName+"].["+procName+"] " 
                print(storedProc,params)
                cursor.execute(storedProc)
            else:
                #Execute Stored Procedure With Parameters
                storedProc = "Exec ["+SchemaName+"].["+procName+"] " + paramList
                logging.info(storedProc)
                logging.info(params)
                print(storedProc,params)
                cursor.execute(storedProc, params)
                
        except Exception as ex:
            logging.error(ex)
            print(ex)
        
        # Iterate the cursor
        if isGetResult == 1:
            row = cursor.fetchone() 
        elif isGetResult == 2:
            sql_data = None
            if cursor.description is not None:
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
    else:
        logging.info("Connection not intialized")
        raise "Error: Database connection failed"


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