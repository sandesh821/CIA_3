#Copyright (c) Microsoft. All rights reserved.
import io
import logging
import requests
import pandas as pd
from modules.apiManager.apiManager import APIManager

class Solcast(APIManager):
    def __init__(self, cfg):
        print(cfg)
        """
        Initializes a Solcast API manager object with the given connection string, container name, API key, and API call.
        
        Parameters:
        cfg (dict): Config Dictionary containing atleast the following values.
            api_call (str): Type of Solcast API call to make. Possible values are "get_forecasts", "get_historical_actuals", and "get_Solcast_Live_data".
            latitude (float): Latitude of the location for which the data is requested.
            longitude (float): Longitude of the location for which the data is requested.
            output_parameters (str): Comma-separated list of parameters to include in the output data. Possible values are "ghi", "dni", "dhi", "air_temperature", and "surface_pressure".
            period (str): Time period for which the data is requested. Possible values are "PT5M", "PT30M", "PT60M", "PT3H", "PT6H", and "PT24H".
            start_date (str, optional): Start date of the time period for which historical data is requested. Should be in the format "YYYY-MM-DDTHH:MM:SSZ". Defaults to None.
            end_date (str, optional): End date of the time period for which historical data is requested. Should be in the format "YYYY-MM-DDTHH:MM:SSZ". Defaults to None.
        """
        super().__init__(cfg)
        self.period = cfg['period']
        self.api_call = cfg['api_call']
    
        # Solcast API endpoint URL for live
        self.live_url = "https://api.solcast.com.au/data/live/radiation_and_weather"
        # Solcast API endpoint URL for forecast
        self.forecast_url = "https://api.solcast.com.au/data/forecast/radiation_and_weather"
        # Solcast API endpoint URL for historical actuals
        self.historical_url = "https://api.solcast.com.au/data/historic/radiation_and_weather"

    
    def getData(self):
        """
        Returns a dataframe containing the data from the specified Solcast API call.
        """

        # Request parameters
        params = {
                "latitude": self.latitude, 
                "longitude": self.longitude,
                "output_parameters": self.output_parameters, 
                "period": self.period, 
                "format": "csv",
                "start_date": self.start_date, 
                "end_date": self.end_date, 
                "time_zone":"utc"
            }

        if self.api_call == "forecasts":
            url = self.forecast_url
        elif self.api_call == "historical":
            url = self.historical_url
        elif self.api_call == "live":
            url = self.live_url

        # Send the API request and get the CSV data
        logging.info(url)
        logging.info(params)
        logging.info(self.api_key)
        headers = {"content-type": "application/json",'Authorization':'Bearer {}'.format(self.api_key)}
        response = requests.get(url, params=params , headers=headers)
        csv_data = response.text
        try:
            # Convert the CSV data to a pandas DataFrame
            df = pd.read_csv(io.StringIO(csv_data))
            return df
        except Exception as ex:
            logging.info(ex)
            logging.info(csv_data)
            return None

        