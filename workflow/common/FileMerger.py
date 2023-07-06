#Copyright (c) Microsoft. All rights reserved.
import pandas as pd
import datetime
import func_utils
from ResamplerMethods import ResamplerMethods

class FileMerger:
    def __init__(self, df_op_resample_list, pred_times_li, look_aheads, step_sizes):
        self._create_merge_metadata(df_op_resample_list)
        self._pred_times_li = pred_times_li
        self._look_aheads = look_aheads
        self._step_sizes = step_sizes

    def _create_merge_metadata(self, df_op_resample_list):
        self._df_li = []; self._is_future_covariate_li = []; self._op_li = []; self._date_time_index=[]; self._forecast_time_index=[]

        if len(df_op_resample_list)%2==0:
            raise ValueError("The length of the dataframe and operator list must be odd!")
        else:
            for i in range(len(df_op_resample_list)):
                d = df_op_resample_list[i]
                if (i % 2 == 0):
                    self._df_li.append(d['df'])
                    self._is_future_covariate_li.append(d['is_future_covariate'])
                    self._date_time_index.append(d['date_time'])
                    self._forecast_time_index.append(d.get('forecast_time', None))
                else:
                    self._op_li.append(df_op_resample_list[i])

    def _joiner(self):
        curr_df = self._df_li[0]
        for i in range(len(self._op_li)):
            if not self._is_future_covariate_li[i] and not self._is_future_covariate_li[i+1]:
                curr_df = curr_df.join(self._df_li[i+1], how=self._op_li[i])
            elif self._is_future_covariate_li[i] and not self._is_future_covariate_li[i+1]:
                #if future covariate
                pass
            elif not self._is_future_covariate_li[i] and self._is_future_covariate_li[i+1]:
                pass
            elif self._is_future_covariate_li[i] and self._is_future_covariate_li[i+1]:
                pass
        return curr_df

    #def _resampler(self):
    #    for df, resample_dict, is_future_covariate, date_time, forecast_time in zip(self._df_li, self._resample_dict_li, self._is_future_covariate_li, self._date_time_index, self._forecast_time_index):
    #        rm = ResamplerMethods(df, resample_dict, self._granularity, date_time, is_future_covariate=is_future_covariate,  forecast_time=forecast_time)
    #        self._df_li_modified.append(rm.get_resampled_df())


    def _shifter(self):
        """
        Start with time gaps in predictions - # of unique gaps = # of models/datasets
        based on starttimes, create a list, then add look-aheads, step-sizes to design dataframes
        Shift the forecast times based on latest time less than or equal to pred time
        :return:
        """
        print("shifter")
        for i, is_future_covariate in zip(range(len(self._df_li)), self._is_future_covariate_li):
            if is_future_covariate:
                for pred_times, look_ahead, step_size in zip(self._pred_times_li, self._look_aheads, self._step_sizes):
                    for pred_time in pred_times:
                        #Handle cases of partial covariates
                        dfn = self._df_li[i]
                        print(dfn)
                        ori_d = datetime.date.today()
                    print(ori_d)
                    d = datetime.datetime.combine(ori_d, datetime.time(23, 55)) + datetime.timedelta(minutes=30) - datetime.datetime.combine(ori_d, datetime.time(0,0))
                    print(d)
                    #& (dfn[self._date_time_index[i]].dt.time<=pred_time + look_ahead)
                    dfn = dfn[(dfn[self._date_time_index[i]].dt.time>=pred_time)] #Forward filter
                    #==pred_time, select x hours ahead
                    #Process
                    self._df_li[i] = dfn
        #Select dates that are available from the latest forecast value
        #Apply groups???

    def order_processing(self):
        self._shifter()
        #return self._joiner()

def reader():
    df = pd.DataFrame({'DateTime': pd.date_range(start='1/1/2018', periods=22, tz='Asia/Tokyo', freq='30min'),
                       'ForecastTime': pd.date_range(start='1/1/2018', periods=22, tz='Asia/Tokyo', freq='30min')})
    df['Value'] = range(len(df))
    df.loc[0:9, 'ForecastTime'] = df.loc[0]['ForecastTime']
    df.loc[10:18, 'ForecastTime'] = df.loc[0]['ForecastTime'] + datetime.timedelta(hours=1)
    df.loc[10:18, 'DateTime'] = df.loc[2:10, 'DateTime'].tolist()
    df.loc[18:, 'ForecastTime'] = df.loc[0]['ForecastTime'] + datetime.timedelta(hours=2)
    df.loc[18:, 'DateTime'] = df.loc[4:7, 'DateTime'].tolist()
    df['DateTime'] = pd.to_datetime(df['DateTime'])
    df['ForecastTime'] = pd.to_datetime(df['ForecastTime'])
    df['Test'] = df['Value']
    return df

if __name__ == '__main__':
    #print(func_utils.get_default_args(math.sqrt))
    df = reader()
    df_past = df[:10]
    df_past = df_past.rename(columns={'Value':'Bulk', 'Test':'Criminal'})
    df_past = df_past[['DateTime', 'Bulk', 'Criminal']]
    #print(df_past)
    fm = FileMerger([
        {'df':df_past, 'is_future_covariate':False, 'date_time':'DateTime'},
        'left',
        {'df': df, 'is_future_covariate': True, 'date_time': 'DateTime', 'forecast_time':'ForecastTime'}
    ], [[datetime.time(2,0,0)]], [datetime.timedelta(hours=3)], [datetime.timedelta(hours=0)])
    fm.order_processing()
