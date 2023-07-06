#Copyright (c) Microsoft. All rights reserved.
import numpy as np
from scipy.stats import circmean
import pandas as pd

class ResamplerUtils:
    def __init__(self):
        pass

    @classmethod
    def cov(self, df, col):
        return df[col].std(ddof=0)/df[col].mean()

    @classmethod
    def circular(self, df, col): #Assumes the original in degrees
        return np.rad2deg(circmean(np.deg2rad(df[col].values)))
