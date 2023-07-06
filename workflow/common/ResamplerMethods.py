#Copyright (c) Microsoft. All rights reserved.
import pandas as pd
# from ResamplerUtils import ResamplerUtils #Used with eval()
from workflow.common.ResamplerUtils import ResamplerUtils #Used with eval()

class ResamplerMethods: #All files must have no index
    def __init__(self, df, sel_cols_dict, granularity, date_time, is_future_covariate = False,  forecast_time=None):
        self._col_order = list(sel_cols_dict.keys())
        print(self._col_order)
        if is_future_covariate:
            self._date_time = date_time
            self._forecast_time = forecast_time
            self._df = df[self._col_order + [self._date_time] + [self._forecast_time]]
            print(self._df)
        else:
            self._df = df.set_index(date_time)
            self._df = self._df[self._col_order]
        self._pandas_supported_funcs = ['mean', 'max', 'sum' , 'min', 'count', 'first', 'last', 'median', 'std', 'var']
        self._circular_funcs = ['circular']
        self._extra_funcs = [func for func in dir(ResamplerUtils) if callable(getattr(ResamplerUtils, func)) and not func.startswith("__") and func not in self._circular_funcs]
        #Use the below variable to populate the dropdown
        self.supported_funcs = self._pandas_supported_funcs + self._extra_funcs + self._circular_funcs
        self._sel_cols_dicts = self._split_selected_cols_dict(sel_cols_dict)
        self._granularity = granularity
        self._is_future_covariate = is_future_covariate

    def _split_selected_cols_dict(self, sel_cols_dict):
        d = {'pandas': {}, 'circular': {}, 'extra': {}}
        for col, resample_method in sel_cols_dict.items():
            if resample_method in self._pandas_supported_funcs:
                d['pandas'][col] = resample_method
            elif resample_method in self._circular_funcs:
                d['circular'][col] = resample_method
            elif resample_method in self._extra_funcs:
                d['extra'][col] = resample_method
            #else:
            #    raise NotImplementedError("The resample method does not exist!")
        return d

    def _future_pandas_resampler(self, df):
        df.set_index(self._date_time, inplace=True)
        return df.resample(self._granularity).agg(self._sel_cols_dicts['pandas'])

    def _resampler_pandas(self):
        if len(self._sel_cols_dicts['pandas'].keys())==0:
            return pd.DataFrame()
        if self._is_future_covariate:
            print('futute Cov')
            print(self._df.groupby(self._forecast_time).apply(lambda x: self._future_pandas_resampler(x)).reset_index().set_index([self._date_time, self._forecast_time]))
            return self._df.groupby(self._forecast_time).apply(lambda x: self._future_pandas_resampler(x)).reset_index().set_index([self._date_time, self._forecast_time])
        else:
            return self._df.resample(self._granularity).agg(self._sel_cols_dicts['pandas'])

    def _future_nonpandas_resampler(self, x, col):
        x.set_index(self._date_time, inplace=True);
        x = x[[col]]
        return x.groupby(pd.Grouper(freq=self._granularity))

    def _resampler_non_pandas(self, method_type):
        df_all = []
        for col, resample_method in self._sel_cols_dicts[method_type].items():
            if self._is_future_covariate:
                val = self._df.groupby(self._forecast_time)#.apply(lambda x: self._future_nonpandas_resampler(x, col)).apply(eval(f"ResamplerUtils.{resample_method}"), args=(col,))
                is_future_li = []
                for name, g in val:
                    g.set_index(self.j, inplace=True)
                    g = g[[col]]
                    ddd = pd.DataFrame({col: pd.Series(g.groupby(pd.Grouper(freq=self._granularity)).apply(eval(f"ResamplerUtils.{resample_method}"),col))})
                    ddd[self._forecast_time] = name
                    ddd.reset_index(inplace=True)
                    ddd.set_index([self._date_time, self._forecast_time], inplace=True)
                    is_future_li.append(ddd)
                ddf = pd.concat(is_future_li)
                df_all.append(ddf)
            else:
                df_all.append(pd.DataFrame({col: pd.Series(self._df.groupby(pd.Grouper(freq=self._granularity)).apply(eval(f"ResamplerUtils.{resample_method}"),col))}))
        if len(df_all)==0:
            return pd.DataFrame()
        return pd.concat(df_all, axis=1)

    def get_resampled_df(self):
        df_pandas = self._resampler_pandas()
        df_circular = self._resampler_non_pandas("circular")
        df_extra = self._resampler_non_pandas("extra")
        return pd.concat([df_pandas, df_circular, df_extra], axis=1)[self._col_order].reset_index()

#------------------------------Class ends here. below tetsing scripts----------------------------------
def tester_non_future_covariate_files():
    import numpy as np
    x = pd.date_range('2017-01-01', periods=100, freq='1min')
    df_x = pd.DataFrame(
        {'DateTime':x, 'price': np.random.randint(50, 100, size=x.shape), 'vol': np.random.randint(1000, 2000, size=x.shape),
        'variance': range(len(x))})
    print(df_x.head(6))
    df_x = df_x.reset_index()
    rm = ResamplerMethods(df_x, {'price': 'mean', 'vol': 'sum', 'variance':'cov'}, "5min", "DateTime")
    dfn = rm.get_resampled_df()
    print(dfn)

    df = pd.DataFrame({'DateTime': [pd.Timestamp(2019, 1, 1, 1, 1, 0), pd.Timestamp(2019, 1, 1, 1, 1, 12),
                                pd.Timestamp(2019, 1, 1, 1, 1, 23),
                                pd.Timestamp(2019, 1, 1, 1, 1, 25), pd.Timestamp(2019, 1, 1, 1, 1, 44),
                                pd.Timestamp(2019, 1, 1, 1, 1, 50)],
                       'A': [5, 7, 9, 8, 11, 6], 'B': [300, 358, 345, 10, 2, 350]})

    rm = ResamplerMethods(df, {'A': 'max', 'B': 'mean'}, "10s", "DateTime")
    dfn = rm.get_resampled_df()
    print(dfn)

    rm = ResamplerMethods(df, {'A': 'cov', 'B': 'circular'}, "10s", "DateTime")
    dfn = rm.get_resampled_df()
    print(dfn)

    rm = ResamplerMethods(df, {'A': 'max', 'B': 'circular'}, "10s", "DateTime")
    dfn = rm.get_resampled_df()
    print(dfn)

    #rm = ResamplerMethods(df, {'A':'adf'}, "10s", "DateTime")
    #dfn = rm.get_resampled_df()
    #print(dfn)

def tester_future_covariate_files():
    df = reader()
    df['Test'] = df['Value']
    print(df)

    col_resample_dict = {'Value': 'cov', 'Test': 'count'}
    df_org = df[:10]
    df_org = df_org[['DateTime', 'Value', 'Test']]

    rm = ResamplerMethods(df_org, col_resample_dict, "1H", "DateTime")
    dfn = rm.get_resampled_df()
    print(dfn)

    rm = ResamplerMethods(df, col_resample_dict, "1H", "DateTime", is_future_covariate=True,
                          forecast_time="ForecastTime")
    dfn = rm.get_resampled_df()
    print(dfn)

def reader():
    import datetime
    df = pd.DataFrame({'DateTime': pd.date_range(start='1/1/2018', periods=18, tz='Asia/Tokyo', freq='30min'),
                       'ForecastTime': pd.date_range(start='1/1/2018', periods=18, tz='Asia/Tokyo', freq='30min')})
    df['Value'] = range(len(df))
    df.loc[0:9, 'ForecastTime'] = df.loc[0]['ForecastTime']
    df.loc[10:, 'ForecastTime'] = df.loc[0]['ForecastTime'] + datetime.timedelta(hours=1)
    df.loc[10:, 'DateTime'] = df.loc[2:9, 'DateTime'].tolist()
    df['DateTime'] = pd.to_datetime(df['DateTime'])
    df['ForecastTime'] = pd.to_datetime(df['ForecastTime'])
    return df

if __name__ == '__main__':
    tester_non_future_covariate_files()
    tester_future_covariate_files()