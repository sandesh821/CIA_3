#Copyright (c) Microsoft. All rights reserved.

#======================================================================
#===================DB Connection configuration========================
#======================================================================

serverKey = 'forecasting-sql-server'
databaseKey = 'forecasting-database'
sqluserKey = 'forecasting-sql-user'
sqlpwdKey = 'forecasting-sql-pwd'
cnxnRetryCount = 5
# Windows Authentication based connection string
#connectionString = 'DRIVER={ODBC Driver 17 for SQL Server};SERVER='+server+';DATABASE='+database+';Trusted_Connection=yes;'

# SQL Server Authentication based connection string
connectionString = 'DRIVER={ODBC Driver 17 for SQL Server};SERVER=$$server$$.database.windows.net;DATABASE=$$database$$;UID=$$username$$;PWD=$$password$$'

# Managed identity connection string
# connectionString = 'DRIVER={ODBC Driver 17 for SQL Server};SERVER='+server+';DATABASE='+database+';Authentication=ActiveDirectoryMsi'