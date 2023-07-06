#Copyright (c) Microsoft. All rights reserved.
import pandas as pd
from datetime import timedelta

class FixTime:
    def __init__(self, forecast_tz, df, datetime_col1: str, datetime_col1_options: dict, datetime_col2: str = None, datetime_col2_options: dict = None):
        self.forecast_tz = forecast_tz
        self.df = df
        self.datetime_col1 = datetime_col1
        self.datetime_col1_options = datetime_col1_options
        self.datetime_col2 = datetime_col2
        self.datetime_col2_options = datetime_col2_options

    @staticmethod
    def filter_future_covariate(df, available_time_col, applicable_time_col):
        return df[df[available_time_col] <= df[applicable_time_col]]

    def apply(self):
        datetime_col1_series = self._apply_each(self.datetime_col1, self.datetime_col1_options)
        datetime_col2_series = None
        if self.datetime_col2 is not None:
            datetime_col2_series = self._apply_each(self.datetime_col2, self.datetime_col2_options)

        return datetime_col1_series, datetime_col2_series

    def _apply_each(self, datetime_col, datetime_col_options):
        if datetime_col_options['type']=='UnixTime':
            new_series = self._convert_from_unix(self.df[datetime_col], datetime_col_options['tz_aware'])
            new_series = self._convert_tz_times(new_series, curr_tz="UTC")
            return new_series
        if datetime_col_options['type']=='Standard':
            if datetime_col_options['tz_aware']:
                new_series = self._remove_tz_info(self.df[datetime_col])
            else:
                new_series = pd.to_datetime(self.df[datetime_col], errors = 'coerce')
            return self._shift_standard_times(new_series, datetime_col_options['tz_info'])
        
        if datetime_col_options['type']=='Timezone' or datetime_col_options['type']=='Local':
            new_series = pd.to_datetime(self.df[datetime_col], errors='coerce')
            if datetime_col_options['tz_aware']:
                new_series = pd.to_datetime(new_series, utc=True)
                new_series = self._convert_to(new_series, self.forecast_tz)
            else:
                new_series = self._convert_tz_times(new_series, curr_tz=datetime_col_options['tz_info'])
            return new_series

    def _convert_from_unix(self, series, unit):
        return pd.to_datetime(series, unit=unit, origin='unix', errors='coerce')

    def _shift_standard_times(self, series, shiftby):
        new_series = series - timedelta(hours=shiftby)
        new_series = self._localize_to(new_series, 'UTC')
        return self._convert_to(new_series, self.forecast_tz)

    def _remove_tz_info(self, series):
        new_series = pd.to_datetime(series, errors='coerce')
        return self._localize_to(new_series, None)

    def _convert_tz_times(self, series, curr_tz=None):
        new_series = self._localize_to(series, curr_tz)
        return self._convert_to(new_series, self.forecast_tz)

    def _localize_to(self, series, localize_str):
        return pd.to_datetime(series).dt.tz_localize(localize_str)

    def _convert_to(self, series, convert_str):
        return pd.to_datetime(series).dt.tz_convert(convert_str)

# if __name__ == '__main__':

    #Case 1 - Unix time
    # df = pd.DataFrame({'Time': [1234567890, 'Dfg', 1345678900]})
    # datetime_col = 'Time'
    # datetime_col_options = {'type':"Unix",'unit':"s"}
    # ft = FixTime("America/Detroit", df, datetime_col, datetime_col_options)
    # print(ft.apply())

    #Case 2 - Standard time without tz_aware
    #df = pd.DataFrame({'Time': ['1982-09-04 1:35:00', 'Dfg', '1982-01-04 1:35:00']})
    # datetime_col = 'Time'
    # datetime_col_options = {'type': "Standard", 'tz_aware': False, 'tz_info':-6}
    
    # ft = FixTime("America/Detroit", df, datetime_col, datetime_col_options)
    # print(ft.apply())
    
    # # Case 3 - Standard time without tz_aware
    # df = pd.DataFrame({'Time': ['1982-09-04 1:35:00 -06:00', 'Dfg', '1982-01-04 1:35:00 -06:00']})
    # datetime_col = 'Time'
    # datetime_col_options = {'type': "Standard", 'tz_aware': True, 'tz_info': -6}
    # ft = FixTime("America/Detroit", df, datetime_col, datetime_col_options)
    # print(ft.apply())

    # #Case 4 - Standard time without tz_aware
    # df = pd.DataFrame({'Time': ['1982-09-04 2:35:00', 'Dfg', '1982-01-04 1:35:00']})
    # datetime_col = 'Time'
    # datetime_col_options = {'type': "Timezone", 'tz_aware': False, 'tz_info':"America/Chicago"}
    # ft = FixTime("America/Detroit", df, datetime_col, datetime_col_options)
    # print(ft.apply())

    # # Case 5 - Standard time without tz_aware
    # df = pd.DataFrame({'Time': ['1982-09-04 2:35:00 -05:00', 'Dfg', '1982-01-04 1:35:00 -06:00']})
    # datetime_col = 'Time'
    # datetime_col_options = {'type': "Timezone", 'tz_aware': True, 'tz_info':"America/Chicago"}
    # ft = FixTime("America/Detroit", df, datetime_col, datetime_col_options)
    # print(ft.apply())

    # #Check for available time<= applicable time
    # df = pd.DataFrame({'AvailableTime': ['2015-09-04 00:00:00 -05:00', '2015-09-04 00:00:00 -05:00', '2015-09-05 00:00:00 -05:00', '2015-09-05 00:00:00 -05:00'],
    #                    'ApplicableTime': ['2015-09-04 00:00:00 -05:00', '2015-09-04 01:00:00 -05:00', '2015-09-04 23:00:00 -05:00', '2015-09-05 00:00:00 -05:00']})
    # datetime_col1 = 'AvailableTime'
    # datetime_col2 = 'ApplicableTime'
    # datetime_col_options = {'type': "Timezone", 'tz_aware': True, 'tz_info': "America/Chicago"}
    # ft = FixTime("America/Detroit", df, datetime_col1, datetime_col_options, datetime_col2, datetime_col_options)
    # df[datetime_col1], df[datetime_col2] = ft.apply()
    # print(ft.filter_future_covariate(df, datetime_col1, datetime_col2))
