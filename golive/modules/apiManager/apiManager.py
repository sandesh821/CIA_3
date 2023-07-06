#Copyright (c) Microsoft. All rights reserved.
import requests
import pandas as pd
from datetime import datetime 
from utilities.azure import keyvaultOperations, blobOperations

class APIManager:
    """
    Class for managing API calls to Solcast and uploading the returned data to Azure Blob Storage.

    Args:
        cfg: 
    """
    def __init__(self, cfg):
        """
        Constructor for the APImanager class.

        Args:
            pred_date (date): Date starting when to pull the data.
        """
        print("Assigning master configurations")
        self.latitude = cfg['latitude']
        self.longitude = cfg['longitude']
        self.output_parameters = cfg['output_parameters']
        self.start_date = cfg['start_date'] if 'start_date' in cfg.keys() else None
        self.end_date = cfg['end_date'] if 'end_date' in cfg.keys() else None
        self.api_key = self.__get_api_key__(cfg["api_name"].lower())
        print(self.api_key)
    
    def __get_api_key__(self,api_name):
        """
            Get API key for the weather api from key vault
        """
        secrets = keyvaultOperations.getSecrets([api_name+"key"])
        return secrets[0]
