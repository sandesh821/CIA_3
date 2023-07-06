#Copyright (c) Microsoft. All rights reserved.
import workflow.index as index 
app = index.app.server
import logging

if __name__ == '__main__':
    index.app.run_server(port="8080",debug = True, loglevel=logging.INFO)
