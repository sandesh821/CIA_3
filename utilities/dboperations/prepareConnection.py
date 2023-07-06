#Copyright (c) Microsoft. All rights reserved.
import utilities.config as config
from utilities.azure import keyvaultOperations

def getSecrets():
    print("Loading secrets")
    try:
        (username, pwd, server, database) = keyvaultOperations.getSecrets([config.sqluserKey,config.sqlpwdKey,config.serverKey,config.databaseKey])
    except Exception as ex:
        print(ex)
        print("Error in reading database secrets!")
    return username, pwd, server, database

def getConnectionString():
    global sqldbconnection
    try:
        print("using existing connection string")
        return sqldbconnection
    except Exception as ex:
        print("loading connection string")
        username, pwd, server, database = getSecrets()
        connection = config.connectionString
        connection = connection.replace("$$username$$",username).replace("$$password$$",pwd)
        connection = connection.replace("$$server$$",server).replace("$$database$$",database)
        sqldbconnection = connection
        return sqldbconnection

# Test script
if __name__ == "__main__":
    getConnectionString()

    

