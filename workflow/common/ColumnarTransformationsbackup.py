#Copyright (c) Microsoft. All rights reserved.
import numpy as np
from workflow.common.ResamplerMethods import ResamplerMethods
# from ResamplerMethods import ResamplerMethods
import pandas as pd
from math import nan

class ColumnarTransformations:
    def __init__(self):
        self.funcs = [func[1:] for func in dir(ColumnarTransformations) if callable(getattr(ColumnarTransformations, func))
                      and not func.startswith("__") and func.startswith("_")]

    def _filter(self, df, column, transformValue, operator):
        local_df = df[[column]]
        if operator=='In':
            local_df[local_df[column].isin(operator)][column] = transformValue
        elif operator=='Out':
            local_df[~local_df[column].isin(operator)][column] = transformValue
        return local_df[column]

    def _scale(self, df, column, transformValue, operator):
        local_df = df[[column]]
        if operator=='Multiply':
            local_df[column] *= transformValue
        elif operator=='Divide':
            local_df[column] /= transformValue
        return local_df[column]

    def _shift(self, df, column, transformValue, operator):
        local_df = df[[column]]
        if operator=='Add':
            local_df[column] -= transformValue
        elif operator=='Subtract':
            local_df[column] -= transformValue
        return local_df[column]

    def _upper_capping(self, df, column, transformValue, operator):
        local_df = df[[column]]
        local_df[local_df[column]>=operator] = transformValue
        return local_df[column]

    def _lower_capping(self, df, column, transformValue, operator):
        local_df = df[[column]]
        local_df[local_df[column]<=operator] = transformValue
        return local_df[column]

    def _replace(self, df, column, transformValue, operator):
        local_df = df[[column]]
        local_df[column] = local_df[column].replace(operator, transformValue)
        return local_df[column]

    def perform_transformations(self, column_transform_operator_dict):
        granularity = column_transform_operator_dict["granularity"]

        for file_id, details in column_transform_operator_dict["file_details"].items():
            df = details['df']
            is_future_covariate = False
            if details['file_type']=="future_covariate":
                is_future_covariate = True
            date_time_index = details['date_time']
            if is_future_covariate:
                forecast_time_index = details['forecast_time']
            else:
                forecast_time_index = None
            resample_dict = {}; interpolation_dict = {}
            for column_name, fields in details['columns'].items():
                for transformation_type, transformValue, operator in fields['transformations']:
                    if transformValue == 'NA' :
                        transformValue = nan
                    df[column_name] = eval(f"self._{transformation_type}")(df, column_name, transformValue, operator)
                new_column_name = file_id + "_" + column_name
                df = df.rename(columns={column_name: new_column_name})
                resample_dict[new_column_name] = fields['resample']
                interpolation_dict[new_column_name] = fields['interpolation']

            rm = ResamplerMethods(df, resample_dict, granularity, date_time_index, is_future_covariate = is_future_covariate, forecast_time=forecast_time_index)
            dfn = rm.get_resampled_df()
            column_transform_operator_dict['file_details'][file_id]['transformed_df'] = dfn
        return column_transform_operator_dict

if __name__ == '__main__':
    #testing code
    ct = ColumnarTransformations()
    column_transform_operator_dict = {}
    column_transform_operator_dict["granularity"] = "1H"
    df = pd.DataFrame({'DateTime':pd.date_range(start='1/1/2018', periods=8, tz='Asia/Tokyo', freq='15min')
        ,'Generation': [1, 4, 3, 2, "d", 8, 3, 4], 'Wind Speed': [-0.1, 0.2, 0.3, 0.4, 0.5, 0.2, 0.3, 0.4,],
                       'Check': [2, 34, 167, 47, 2, 44, 23, 1], 'Get': [2, 34, 12, 8, 5, 14, 10, 9]})
    print(df)
    column_transform_operator_dict["file_details"] = {'file1':{'df':df, 'file_type':'past_covariate', 'date_time':'DateTime',
                                            'columns':{'Generation':{'transformations':[("replace",2,"d"),
                                                                                        ("scale", 2, "Multiply")],
                                                                     'resample':'mean', 'interpolation':'linear'}}}}
    print(ct.funcs)
    d = ct.perform_transformations(column_transform_operator_dict)
    print(d['file_details']["file1"]["transformed_df"])
