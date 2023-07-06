#Copyright (c) Microsoft. All rights reserved.
import numpy as np
from fancyimpute import IterativeImputer, KNN

class InterpolatorUtils:

    @classmethod
    def circular(cls, df, col_name, freq):
        df[col_name] = np.rad2deg(np.unwrap(np.deg2rad(df[col_name])))
        df = df.resample(freq).mean()
        df[col_name] = df[col_name].interpolate()
        df[col_name] %= 360
        return df[col_name]

    @classmethod
    def knn(cls, df, col_names):
        knn_imputer = KNN()
        return knn_imputer.fit_transform(df[col_names])

    @classmethod
    def mice(cls, df, col_names):
        mice_imputer = IterativeImputer()
        return mice_imputer.fit_transform(df[col_names])