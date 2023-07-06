#Copyright (c) Microsoft. All rights reserved.
import pandas as pd
import numpy as np

import plotly.express as px
from  workflow.common.HexPlotly import HexPlotly
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly_resampler import FigureResampler
import plotly.io as pio
import plotly.figure_factory as ff
from plotly.subplots import make_subplots
from  workflow.common import DomainFactory
from workflow.common.MainPlotly import MainPlotly


class MultivariatePlotly(MainPlotly):
    def __init__(self, df, columns, index, domain_name, tag_col_dict):
        self._df = df
        self._columns = columns
        self._index = index
        self._domain_name = domain_name
        self._domain_class = DomainFactory.domainFactory(domain_name)
        print((self._df, self._columns, tag_col_dict))
        self._domain_obj = self._domain_class(self._df, self._columns, tag_col_dict)
        self._domain_funcs = [func for func in dir(self._domain_class) if callable(getattr(self._domain_class, func)) and not func.startswith("_") and not func.__contains__("__")]
        self._multivariate_funcs = [func for func in dir(MultivariatePlotly) if callable(getattr(MultivariatePlotly, func)) and not func.startswith("_") and not func.__contains__("__")]
        self.funcs = self._domain_funcs + self._multivariate_funcs


    def line_graph(self, sel_cols=None, need_subplot=False):
        sel_cols = super()._clean_cols(sel_cols, self._columns)
        fig = FigureResampler(go.Figure())

        if need_subplot:
            count = len(sel_cols)
            fig = make_subplots(rows=len(sel_cols), cols=1, vertical_spacing=0.065, shared_xaxes=True)
            for col in sel_cols:
                fig.add_trace(go.Scatter(x=list(df.index), y=list(df[col]), name=col), sel_cols.index(col) + 1, 1);
            params = {f"xaxis{count}_rangeslider_visible": True, f"xaxis{count}_type": "date"}
        else:
            for col in sel_cols:
                fig.add_trace(go.Scatter(x=self._df.index, y=self._df[col], name=col))
            params = {f"xaxis_rangeslider_visible": True, f"xaxis_type": "date"}

        fig.update_layout(xaxis=dict(rangeselector=dict(buttons=[
            dict(count=1, label="1m", step="month", stepmode="backward"),
            dict(count=6, label="6m", step="month", stepmode="backward"),
            dict(count=1, label="YTD", step="year", stepmode="todate"),
            dict(count=1, label="1y", step="year", stepmode="backward"),
            dict(step="all")]), type="date"), **params);

        return fig

    def heatmap_graph(self, sel_cols=None, mat=None, fig_params={}, text_visible=True, rounding=3):
        if mat is None:
            sel_cols = super()._clean_cols(sel_cols, self._columns)
            mat = np.round(self._df[sel_cols].corr(), rounding)
            return px.imshow(mat, x=mat.columns, y=mat.columns, text_auto=text_visible, zmin=-1, zmax=1, **fig_params)
        else:
            return px.imshow(mat, x=mat.columns, y=mat.columns, text_auto=text_visible)

    def cdf_graph(self, sel_cols=None, percentile_bands=[0.1,0.5,0.9], marginal="rug", start_date=None, end_date=None): #marginal = rug, violin, box
        sel_cols = super()._clean_cols(sel_cols, self._columns)
        df_local = self._df[sel_cols]
        if start_date is not None and end_date is not None:
            df_local = super()._data_selector(self._df, self._index, start_date=start_date, end_date=end_date)

        fig = px.ecdf(df_local, x=sel_cols, marginal=marginal)
        for percentile_band in percentile_bands:
            fig.add_hline(y=percentile_band, name=percentile_band * 100, line_dash="dash", row=1)
        return fig

    def pdf_graph(self, sel_cols = None, start_date=None, end_date=None):
        sel_cols = super()._clean_cols(sel_cols, self._columns)
        df_local = self._df
        if start_date is not None and end_date is not None:
            df_local = super()._data_selector(self._df, self._index, start_date=start_date, end_date=end_date)

        return ff.create_distplot(df_local[sel_cols].T.values, sel_cols)

    def hexbin_graph(self, x_col, y_col, gridsize=100, bins=None, cmap=plt.cm.Blues, width=850, height=700):
        hp = HexPlotly(self._df[x_col], self._df[y_col], gridsize=gridsize, bins= bins, cmap=cmap)
        return hp.plotter(width=width, height=height)

    def scatter_graph(self, x_col, y_col, hue_col=None, scatter_type="color", hover_data=None):
        if hue_col is None:
            fig = px.scatter(self._df, x=x_col, y=y_col, hover_data=hover_data)
        else:
            if scatter_type=="size":
                fig = px.scatter(self._df, x=x_col, y=y_col, size=hue_col, hover_data=hover_data)
            elif scatter_type=="color":
                fig = px.scatter(self._df, x=x_col, y=y_col, color=hue_col, hover_data=hover_data)
        return fig

    def box_plot(self, x_cols, y_col, hue_col=None):
        return px.box(self._df, x = x_cols, y=y_col, color=hue_col)

    def create__table(self, sel_funcs):
        domain_sel_cols = []
        fig_list = []; relevent_cols = []; params = []
        for sel_func in sel_funcs:
            if sel_func in self._multivariate_funcs:
                if sel_func =="line_graph" or sel_func=="cdf_graph" or sel_func=="pdf_graph" or sel_func=="heatmap_graph":
                    fig_list.append(eval(f"self.{sel_func}")())
                    relevent_cols.append(self._columns)
                    params.append({})
                elif sel_func=="box_plot":
                    if len(self._columns) >= 2:
                        fig_list.append(eval(f"self.{sel_func}")(x_cols=self._columns[:-1], y_col=self._columns[-1]))
                        relevent_cols.append({"x_cols":self._columns[:-1], "y_col":self._columns[-1]})
                        params.append({})
                else:
                    if len(self._columns)>=2:
                        fig_list.append(eval(f"self.{sel_func}")(x_col=self._columns[0], y_col=self._columns[1]))
                        relevent_cols.append({"x_col": self._columns[0], "y_col": self._columns[1]})
                        params.append({})
            elif sel_func in self._domain_funcs:
                domain_sel_cols.append(sel_func)

            sel_funcs_domain , fig_list_domain, relevent_cols_domain, params_domain = self._domain_obj.create__table(domain_sel_cols)
            fig_list.extend(fig_list_domain)
            relevent_cols.extend(relevent_cols_domain)
            sel_funcs.extend(sel_funcs_domain)
            params.extend(params_domain)

        return sel_funcs, relevent_cols, params, fig_list


def reader():
    df = pd.read_csv("../AAPL.csv", parse_dates=True, index_col="Date")
    df['Year'] = df.index.year
    df['Month'] = df.index.month
    df['DayOfWeek'] = df.index.dayofweek
    df['Date'] = df.index
    return df

# if __name__ == '__main__':
#     df = pd.read_csv("C:\\Users\\sriyengar\\Downloads\\Australia\\WundergroundAirport_Clean\\weather_YWHA.csv")
#     df = df.fillna(0)
#     mp = MultivariatePlotly(df, ['WindSpeed','gust','WindDirection'], index="Date", domain_name="wind", tag_col_dict={'Wind Speed':["WindSpeed"], "Wind Direction":["WindDirection"], "Wind Gust":["gust"], "Generation":["gust"]})
#     print(mp.funcs)
#     sel_funcs, relevent_cols, params, fig_list = mp.create__table(['box_plot', 'cdf_graph', 'heatmap_graph', 'hexbin_graph', 'line_graph', 'pdf_graph', 'power_curve_hexbin'])
#     for fig in fig_list:
#         fig.show()


