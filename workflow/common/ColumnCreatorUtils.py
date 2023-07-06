#Copyright (c) Microsoft. All rights reserved.
import pandas as pd
import numpy as np
from . import virtualsensors
from . import  MetricsUtils

class ColumnCreatorUtils:
    numpy_funcs = {'argmax':{}, 'argmin':{}, 'max':{}, 'mean':{}, 'median':{}, 'min':{}, 'percentile':{'q':50}, 'prod':{}, 'std':{}, 'sum':{}, 'var':{}}
    pandas_funcs = {'count':{}, 'max':{}, 'mean':{}, 'median':{}, 'min':{}, 'nunique':{}, 'quantile':{'q':0.5}, 'std':{}, 'sum':{}, 'var':{}}
    custom_funcs = {'sin' : {} , 'cos' : {}}
    virtualsensors_funcs = {'virtualsensor' : {}}
    all_funcs = {'numpy':numpy_funcs, 'pandas':pandas_funcs , 'custom' : custom_funcs , 'virtualsensors' : virtualsensors_funcs }


    @classmethod 
    def _virtualsensors(self, df, selected_columns, func , params):
        col = params['reference_col']+'_virtual'
        if func == 'virtualsensor' :
            colocation_dict = {params['reference_col']:selected_columns}
            vs = virtualsensors.KLDivergenceOrder(df, colocation_dict, runs=20)
            d = vs.get_virtual_sensors()
            print(d)
            df = d[col][[col]]
        return df

    @classmethod
    def _numpy(self, df, selected_columns, func, params):
        if func=="percentile" and params=={}:
            params['q'] = 50
        params['axis'] = 1
        s = df[selected_columns].apply(eval(f"np.{func}"), **params)
        return self._check_size(df, s)

    @classmethod
    def _pandas(self, df, selected_columns, func, params):
        if func=="quantile" and params=={}:
            params['q'] = 0.5
        params['axis'] = 1
        local_df = df[selected_columns]
        s = eval(f"local_df.{func}")(**params)
        return self._check_size(df, s)
    
    @classmethod
    def _custom(self, df, selected_columns, func, params):
        if func=="sin" and params=={}:
            functionName ='extract_sin'
        if func=="cos" and params=={}:
            functionName ='extract_cos'
        local_df = df[selected_columns]
        s = eval(f"self.{functionName}(local_df[selected_columns])")
        return s

    @classmethod
    def _check_size(self, df, transformed_series):
        if transformed_series.shape==(df.shape[0],):
            return transformed_series
        else:
            raise ValueError(f"Shape mismatch!")
        
    @classmethod
    def extract_sin(self,local_df):
        local_df = local_df.apply(np.sin)
        local_df = np.round(local_df,decimals = 2) 
        return local_df
    
    def extract_cos(self,local_df):
        local_df = local_df.apply(np.cos)
        local_df = np.round(local_df,decimals = 2) 
        return local_df
    
    
