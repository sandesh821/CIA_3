#Copyright (c) Microsoft. All rights reserved.
import pandas as pd
import numpy as np
from workflow.common.InterpolatorMethods import *
from workflow.common.InterpolatorUtils import *
class InterpolatorMethods:
    def __init__(self):
        self.pandas_methods = ['fillna','linear','krogh', 'piecewise_polynomial', 'spline', 'pchip', 'akima', 'cubicspline',
                               'nearest', 'zero', 'slinear', 'quadratic', 'cubic', 'spline', 'barycentric', 'polynomial']
        self.extra_methhods = [func for func in dir(InterpolatorUtils) if callable(getattr(InterpolatorUtils, func)) and not func.startswith("__")]

    def fillna(cls, df, col_name, **params):
        return df[col_name].fillna(params)

    def interpolate_all(self, df, interpolation_li):
        print(interpolation_li)
        for params in interpolation_li:
            if params['family_func']=="pandas":
                if params['method']=='fillna':
                    self.fillna(df, params['col'], **params['vals'])
                else:
                    print(params['col'],params['method'],params['vals'])
                    df[params['col']] = df[params['col']].interpolate(method=params['method'], **params['vals'])
            elif params['family_func']=="others":
                df[params['col']] = eval(f"InterpolatorUtils.{params['method']}")(df, params['col'], **params['vals'])
        return df

def reader():
    df = pd.read_csv("../AAPL.csv", parse_dates=True, index_col="Date")
    nan_mat = np.random.random(df.shape)<0.5
    df = df.mask(nan_mat)
    return df

if __name__ == '__main__':
    df = reader()
    im = InterpolatorMethods()
    print(im.pandas_methods)
    df = im.interpolate_all(df, [{'family_func':'pandas', 'col':["Open"], 'method':'linear', 'vals':{'limit':1}},
                                  {'family_func':'pandas', 'col':["Low"], 'method': 'fillna', 'vals':{'limit':1, 'value':5}},
                                 {'family_func': 'others', 'col': ["Close"], 'method': 'knn', 'vals': {}},
                                  {'family_func':'others', 'col':["High"], 'method':'circular', 'vals': {'freq':'1D'}}])
    print(df[['Open','Close', 'Low', 'High']])
