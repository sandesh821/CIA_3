#Copyright (c) Microsoft. All rights reserved.
import WeatherService
import requests
import pandas as pd
import json
import os
import time

class DarkSky(WeatherService):
    def __init__(self, download_path, **dict_params):
        serviceName = "DarkSky"
        WeatherService.__init__(serviceName, download_path)
        self._baseURL = "https://api.darksky.net/forecast/"
        self._granularities = ["currently", "minutely", "hourly", "daily"]
        if dict_params is None:
            self._params = {'default_wait_time': 0.2}
        else:
            self._params = dict_params

    def _send_request(self, site, **kwargs):
        if kwargs.get('unixtime') is None:
            unixtime = int(time.time())
            ext = f"{self._secret_token}/{site.latitude},{site.longitude}"
        else:
            unixtime = kwargs.get('unixtime')
            ext = f"{self._secret_token}/{site.latitude},{site.longitude},{unixtime}"
        fin_url = self._baseURL + ext + "?units=si"
        resp = requests.get(fin_url)
        output = open(self.download_path_raw + f"{unixtime}.json", 'wb')
        output.write(resp.content)
        output.close()

    def create_cleaned_data(self):
        """
        :return:
        """
        all_data = {}
        filenames = [file for file in os.listdir(self.download_path_raw) if ".json" in file]
        for granularity in self._granularities:
            all_data[granularity] = []
        for filename in filenames:
            f = open(self.download_path_raw + filename, "r")
            data = json.loads(f.read())
            for granularity in self._granularities:
                for ind_di in data[granularity]['data']:
                    ind_di[self._pred_time_col_name] = str(filename.split(".")[0])
                    all_data[granularity].append(ind_di)
            f.close()
        for granularity, list_dict in all_data.items():
            df = pd.DataFrame(list_dict)
            df.to_csv(self.download_path_clean + "_".join([granularity, self._default_filename]), index=None)

    def get_current_forecasts(self, site):
        self._send_request(site)

    def get_historical_forecasts(self, site, start_date, end_date, frequency='1D'):
        dates = pd.date_range(start=start_date, end=end_date, freq=frequency, tz=site.timezone).tolist()
        unixtimes = [int(date.timestamp()) for date in dates]
        for unixtime in unixtimes:
            if os.path.isfile(self.download_path_raw + f"{unixtime}.json"):
                continue
            else:
                self._send_request(site, unixtime=unixtime)
                time.sleep(self._params['default_wait_time'])

if __name__ == '__main__':
    pass
