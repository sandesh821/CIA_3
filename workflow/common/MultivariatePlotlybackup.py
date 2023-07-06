#Copyright (c) Microsoft. All rights reserved.
import pandas as pd
import numpy as np

import plotly.express as px
from workflow.common.HexPlotly import HexPlotly
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly_resampler import FigureResampler
import plotly.io as pio
import plotly.figure_factory as ff
from plotly.subplots import make_subplots

from workflow.common.MainPlotly import MainPlotly

class MultivariatePlotly(MainPlotly):
    def __init__(self, df, columns):
        self.df = df
        self.columns = columns
        self.index = df.index

    def line_graph(self, sel_cols=None, need_subplot=False):
        sel_cols = super()._clean_cols(sel_cols, self.columns)
        fig = FigureResampler(go.Figure())

        if need_subplot:
            count = len(sel_cols)
            fig = make_subplots(rows=len(sel_cols), cols=1, vertical_spacing=0.065, shared_xaxes=True)
            for col in sel_cols:
                fig.add_trace(go.Scatter(x=list(df.index), y=list(df[col]), name=col), sel_cols.index(col) + 1, 1);
            params = {f"xaxis{count}_rangeslider_visible": True, f"xaxis{count}_type": "date"}
        else:
            for col in sel_cols:
                fig.add_trace(go.Scatter(x=self.df.index, y=self.df[col], name=col))
            params = {f"xaxis_rangeslider_visible": True, f"xaxis_type": "date"}

        fig.update_layout(xaxis=dict(rangeselector=dict(buttons=[
            dict(count=1, label="1m", step="month", stepmode="backward"),
            dict(count=6, label="6m", step="month", stepmode="backward"),
            dict(count=1, label="YTD", step="year", stepmode="todate"),
            dict(count=1, label="1y", step="year", stepmode="backward"),
            dict(step="all")]), type="date"), **params);

        return fig

    def heatmap_graph(self, mat=None, fig_params={}, sel_cols=None, text_visible=True, rounding=3):
        if mat is None:
            sel_cols = super()._clean_cols(sel_cols, self.columns)
            mat = np.round(self.df[sel_cols].corr(), rounding)
            return px.imshow(mat, x=mat.columns, y=mat.columns, text_auto=text_visible, zmin=-1, zmax=1, **fig_params)
        else:
            px.imshow(mat, x=mat.columns, y=mat.columns, text_auto=text_visible)

    def cdf_graph(self, sel_cols=None, percentile_bands=[0.1,0.5,0.9], marginal="rug", start_date=None, end_date=None): #marginal = rug, violin, box
        sel_cols = super()._clean_cols(sel_cols, self.columns)
        df_local = self.df[sel_cols]
        if start_date is not None and end_date is not None:
            df_local = super()._data_selector(self.df, self.index, start_date=start_date, end_date=end_date)

        fig = px.ecdf(df_local, x=sel_cols, marginal=marginal)
        for percentile_band in percentile_bands:
            fig.add_hline(y=percentile_band, name=percentile_band * 100, line_dash="dash", row=1)
        return fig

    def pdf_graph(self, sel_cols = None, start_date=None, end_date=None):
        sel_cols = super()._clean_cols(sel_cols, self.columns)
        df_local = self.df
        if start_date is not None and end_date is not None:
            df_local = super()._data_selector(self.df, self.index, start_date=start_date, end_date=end_date)

        return ff.create_distplot(df_local[sel_cols].T.values, sel_cols)

    def hexbin_graph(self, x_col, y_col, gridsize=100, bins=None, cmap=plt.cm.Blues, width=850, height=700):
        hp = HexPlotly(self.df[x_col], self.df[y_col], gridsize=gridsize, bins= bins, cmap=cmap)
        return hp.plotter(width=width, height=height)

    def scatter_graph(self, x_col, y_col, hue_col=None, scatter_type="color", hover_data=None):
        if hue_col is None:
            fig = px.scatter(self.df, x=x_col, y=y_col, hover_data=hover_data)
        else:
            if scatter_type=="size":
                fig = px.scatter(self.df, x=x_col, y=y_col, size=hue_col, hover_data=hover_data)
            elif scatter_type=="color":
                fig = px.scatter(self.df, x=x_col, y=y_col, color=hue_col, hover_data=hover_data)
        return fig

    def box_plot(self, x_cols, y_col, hue_col=None):
        return px.box(self.df, x = x_cols, y=y_col, color=hue_col)


def reader():
    df = pd.read_csv("../AAPL.csv", parse_dates=True, index_col="Date")
    df['Year'] = df.index.year
    df['Month'] = df.index.month
    df['DayOfWeek'] = df.index.dayofweek
    df['Date'] = df.index
    return df

if __name__ == '__main__':
    df = reader()
    mp = MultivariatePlotly(df, ["Open","High","Low","Close"], index="Date")
    fig = mp.line_graph(need_subplot=True)
    fig.show()
    #fig = mp.hexbin_graph("Open", "Close")#, hue_col="Low")
    fig = mp.box_plot(x_cols= ["Year"], y_col="Open")
    fig.show()