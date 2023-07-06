#Copyright (c) Microsoft. All rights reserved.
import numpy as np
import pandas as pd
import plotly.express as px 
from workflow.common.MainPlotly import *
import plotly.figure_factory as ff

import seaborn as sns
import pylab as plt
from kneed import KneeLocator 
from workflow.common.InterpolatorMethods import InterpolatorMethods

# Missing values - heatmap, between missing values, knee point

class MissingvalueEDA(MainPlotly):
    def __init__(self, df):
        self.df = df

    def missing_heatmap(self, sel_cols=None):
        sel_cols = super()._clean_cols(sel_cols, self.df.columns)
        data_df = ~self.df[sel_cols].isna().astype(int) + 2
        fig = px.imshow(data_df, zmin=0, zmax=1, color_continuous_scale="greys",aspect='auto')
        for val in range(len(sel_cols)):
            fig.add_vline(x=val+0.5, row=1, line_color="#ffffff")
        fig.update_coloraxes(showscale=False)
        #Adjust hover text
        return fig

    def continuous_missing_distribution(self, col, threshold=0): #50
        cont_missing = pd.DataFrame(self.df[col].isnull().astype(int).groupby(self.df[col].notnull().astype(int).cumsum()).sum())
        cont_missing.index.names = ['index']
        cont_missing = cont_missing[cont_missing[col] > threshold]
        fig = px.histogram(cont_missing, x=col, nbins=min(2, cont_missing[col].max()), marginal="rug") # bins  nbins=min(2, cont_missing[col].max())
        return fig

    def _knee_point(self, x, y, col):
        kneedle = KneeLocator(x, y, S=1.0, curve="concave", direction="increasing")
        # kneedle.plot_knee_normalized()
        kneedle.plot_knee()
        print(kneedle.knee)

    def knee_point_cal(self, interpolate_cols, limit_val=50):
        im = InterpolatorMethods()
        im.interpolate_all(self.df, im.interpolate_all)
        pass
        """
        for col in df.columns:
            limit_lst = list(range(1, limit_val))
            no_of_records = []
            for i in limit_lst:

                interpolated_df = AutoEDAObj.interpolate_impute(interpolate_cols, data)
                no_of_records.append(len(interpolated_df))
            knee_point_df = pd.DataFrame({'limit': limit_lst, 'no_of_records': no_of_records})
        """

def reader():
    df = pd.read_csv("../AAPL.csv", parse_dates=True, index_col="Date")
    nan_mat = np.random.random(df.shape)<0.5
    df = df.mask(nan_mat)
    return df

if __name__ == '__main__':
    df = reader()
    me = MissingvalueEDA(df)
    #fig = me.missing_heatmap()
    #fig.show()

    fig = me.continuous_missing_distribution("Open")
    fig.show()