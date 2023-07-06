#Copyright (c) Microsoft. All rights reserved.
import numpy as np
import pandas as pd

class PrepopulateTransformations:
    def __init__(self, df, file_id, forecast_domain, capacity=None):
        self._col_tag_dict = {'solar': ["Generation","Global Horizontal Irradiance", "Direct Normal Irradiance",
                              "Diffuse Horizontal Irradiance", "Global Tilted Irradiance",
                              "Plane of Array Irradiance", "Direct (Beam) Horizontal Irradiance" 
                              "Generation", "Visibility", "Solar Altitude", "Solar Azimuth",
                              "Cloud Opacity", "Module Temperature", "Ambient Temperature",
                              "Tilt", "Orientation", "Precipitation", "Snow Depth", "Wind Speed",
                              "Wind Direction", "Dew Point", "Relative Humidity", "Surface Pressure",
                              "Overall Online Capacity"],
                    'wind': ["Generation", "Wind Speed", "Wind Direction", "Wind Gust",
                            "Overall Online Capacity"],
                    'demand': ["Ambient Temperature", "Precipitation", "Snow Depth", "Wind Speed",
                              "Wind Direction", "Dew Point", "Relative Humidity","Surface Pressure"],
                    'price': ["Volume Traded", "Suppy", "Demand", "Ambient Temperature",
                              "Precipitation", "Snow Depth", "Wind Speed", "Wind Direction",
                              "Dew Point", "Relative Humidity", "Surface Pressure"]}
        self._df = df
        self._file_id = file_id
        self._forecast_domain = forecast_domain
        self._accepted_negative = ["Dew Point","Ambient Temperature","Solar Altitude","Module Temperature"]
        self._accepted_max_ceiling = {"Generation":capacity, "Relative Humidity":100, "Wind Direction":360,
                                      "Global Horizontal Irradiance":1000, "Direct Normal Irradiance":1000,
                                     "Diffuse Horizontal Irradiance":1000, "Global Tilted Irradiance":1000,
                                     "Plane of Array Irradiance":1000, "Direct (Beam) Horizontal Irradiance":1000}

        #Public variable
        self.accepted_tags = self._col_tag_dict[self._forecast_domain]

    def _capping_transform(self):
        d = []
        if self._tag not in self._accepted_negative and self._tag in self.accepted_tags:
            d.append({'transformation':'lower_capping','transformValue':'NA', 'operator': 0}) #np.NaN
        if self._tag in self._accepted_max_ceiling.keys():
            d.append({'transformation':'upper_capping','transformValue':self._accepted_max_ceiling[self._tag], 'operator': self._accepted_max_ceiling[self._tag]})
        return d

    def _replace_transform(self):
        local_df = self._df[[self._column]]
        replace_li = local_df[~local_df.applymap(lambda x: isinstance(x, (int, float)))].dropna()[self._column].unique().tolist()
        d = []
        for replace in replace_li:
            d.append({'transformation':'replace','transformValue':np.NaN, 'operator': replace})
        return d

    def _de_mode(self):
        return NotImplementedError("Yet to Implement!")

    def get_list_transforms(self, column, tag=None):
        self._column = column
        self._tag = tag
        list_transforms = []
        list_transforms.extend(self._capping_transform())
        list_transforms.extend(self._replace_transform())
        return {column:list_transforms}

if __name__ == '__main__':
    df = pd.DataFrame({'Generation': [1, 'a', 'bad', 'bad', 5],
                       'Wind Speed': [-0.1, 0.2, 0.3, 0.4, 0.5],
                       'Check': [10002,34, 167, 'ola',2]})
    for col in df.columns:
        pt = PrepopulateTransformations(df, "SCADA", "Wind", capacity=4)
        tags = pt.accepted_tags
        if col not in tags:
            li = pt.get_list_transforms(col)
        else:
            li = pt.get_list_transforms(col, col)
        print(li)