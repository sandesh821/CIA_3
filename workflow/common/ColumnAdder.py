#Copyright (c) Microsoft. All rights reserved.
import pandas as pd
from collections import OrderedDict
from workflow.common.ColumnCreatorUtils import ColumnCreatorUtils

class ColumnAdder:
    def __init__(self, df):
        self._df = df
        self.funcs = ColumnCreatorUtils.all_funcs #[func for func in dir(ColumnCreatorUtils) if callable(getattr(ColumnCreatorUtils, func)) and not func.startswith("__")]

    def create_columns(self, column_creator_dict):
        cols = []
        for column, settings in column_creator_dict.items():
            self._df[column] = eval(f"ColumnCreatorUtils._{settings['func_family']}")(self._df, settings['selected_columns'], settings['func'], settings['params'])
            tag = settings.get('tag', None)
            cols.append({'Column_name': column, 'Tag': tag, 'Interpolation': settings['interpolation_method']})
        return self._df, cols


if __name__ == '__main__':
    df = pd.DataFrame({'Generation': [1, 4, 3, 2, 5],'Wind Speed': [-0.1, 0.2, 0.3, 0.4, 0.5],
                       'Check': [2, 34, 167, 47, 2], 'Get': [2, 34, 12, 8, 5]})

    column_creator_dict = OrderedDict({"CheckGet":{'selected_columns':['Check', 'Get'], 'interpolation_method':'linear','func_family':'numpy', 'func':'percentile', 'params':{'q':75}},
                                       "Features":{'selected_columns':['Generation', 'Wind Speed'], 'tag':'Generation', 'interpolation_method':'linear','func_family':'pandas', 'func':'sum', 'params':{}}})

    ca = ColumnAdder(df)
    df = ca.create_columns(column_creator_dict)
    print(df)

