#Copyright (c) Microsoft. All rights reserved.
import numpy as np
import pandas as pd
import math
from workflow.common.MainPlotly import MainPlotly
import plotly.express as px
from  workflow.common.HexPlotly import HexPlotly
import matplotlib.pyplot as plt

class WindPlotly(MainPlotly):
    def __init__(self, df, columns, tag_col_dict):
        #Get from DB
        self._tags = ["Generation", "Wind Speed", "Wind Direction", "Wind Gust", "Overall Online Capacity"]
        self._df = df
        self._columns = columns
        self._tag_col_dict = tag_col_dict
        print(self._tag_col_dict )

    def _degToCompass(self, num, dirs):
        if math.isnan(num):
            return np.NaN
        val = int((num / 22.5) + .5)
        return dirs[(val % 16)]

    def _adjust_windspeed_cols(self, include_wind_gust = False):
        windspeed_cols = self._tag_col_dict["Wind Speed"]  # + self._tag_col_dict["Wind Gust"]
        if include_wind_gust:
            windspeed_cols += self._tag_col_dict["Wind Gust"]
        return windspeed_cols

    def wind_rose(self, windspeed_col, winddirection_col):
        df = self._df
        dirs = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
        df["Cardinal"] = df[winddirection_col].apply(lambda x: self._degToCompass(x, dirs))

        dfn_all = []
        for cardinal in dirs:
            df_sel = df[df['Cardinal'] == cardinal][[windspeed_col]]
            bins = np.array([0, 4, 8, 12, 16, 20, 24, 28, 32, 36, 40])

            print(pd.cut(df[windspeed_col], bins))
            print(df_sel.groupby(pd.cut(df[windspeed_col], bins)).count().values)

            vals = df_sel.groupby(pd.cut(df[windspeed_col], bins)).count().values.T[0]
            nbins = df_sel.groupby(pd.cut(df[windspeed_col], bins)).count().index.astype(str).str.replace("(",
                                                                                                        "").str.replace(
                "]", "").str.replace(", ", "-").to_list()
            dfn = pd.DataFrame({'Bins': nbins, 'Count': vals})
            dfn['Cardinal'] = cardinal
            dfn_all.append(dfn)
        dfs = pd.concat(dfn_all)
        fig = px.bar_polar(dfs, r="Count", theta="Cardinal",
                           color="Bins", template="plotly_dark",
                           color_discrete_sequence=px.colors.sequential.Plasma_r)
        return fig

    def _wind_rose_list(self, include_wind_gust = False):
        windspeed_cols = self._adjust_windspeed_cols(include_wind_gust)
        winddirection_cols = self._tag_col_dict["Wind Direction"]
        fig_li = []; relevant_cols=[]; params = []
        for winddirection_col in winddirection_cols:
            for windspeed_col in windspeed_cols:
                fig = self.wind_rose(windspeed_col, winddirection_col)
                fig_li.append(fig)
                relevant_cols.append({"windspeed_col": windspeed_col, "winddirection_col": winddirection_col})
                params.append({})
        return fig_li, relevant_cols, params

    def power_curve_hexbin(self, windspeed_col, generation_col, gridsize=20, bins=None, cmap=plt.cm.Blues, width=850, height=700):
        hp = HexPlotly(self._df[windspeed_col], self._df[generation_col], gridsize=gridsize, bins=bins, cmap=cmap)
        return hp.plotter(width=width, height=height)

    def _power_curve_hexbin_list(self, include_wind_gust=False):
        windspeed_cols = self._adjust_windspeed_cols(include_wind_gust)
        generation_cols = self._tag_col_dict["Generation"]
        fig_li = []; relevant_cols=[]; params = []
        for generation_col in generation_cols:
            for windspeed_col in windspeed_cols:
                fig = self.power_curve_hexbin(windspeed_col, generation_col)
                fig_li.append(fig)
                relevant_cols.append({"windspeed_col":windspeed_col, "generation_col":generation_col})
                params.append({})
        return fig_li, relevant_cols, params

    def power_curve_box(self, windspeed_col, generation_col):
        px.box(self._df, x=windspeed_col, y=generation_col, color=None)

    def _power_curve_box_list(self, include_wind_gust=False):
        windspeed_cols = self._adjust_windspeed_cols(include_wind_gust)
        generation_cols = self._tag_col_dict["Generation"]
        fig_li = []; relevant_cols=[]; params = []

        for generation_col in generation_cols:
            for windspeed_col in windspeed_cols:
                fig = self.power_curve_box(windspeed_col, generation_col)
                fig_li.append(fig)
                relevant_cols.append({"windspeed_col":windspeed_col, "generation_col":generation_col})
                params.append({})
        return fig_li, relevant_cols, params  

    def create__table(self, sel_funcs):
        fig_list_all = []; relevent_cols_all = []; params_all = [] ; sel_funcs_new = []
        for sel_func in sel_funcs:
            fig_li, relevent_cols, params = eval(f"self._{sel_func}_list")()
            sel_funcs_new.extend([sel_func] * len(fig_li)) 
            fig_list_all.extend(fig_li)
            relevent_cols_all.extend(relevent_cols)
            params_all.extend(params)
        return sel_funcs_new,fig_list_all, relevent_cols_all, params_all

    def update__table(self):
        pass
# if __name__ == '__main__':
#     df = pd.read_csv("C:\\Users\\sriyengar\\Downloads\\Australia\\WundergroundAirport_Clean\\weather_YWHA.csv")
#     wp = WindPlotly(df, df.columns, {'Wind Speed':["WindSpeed"], "Wind Direction":["WindDirection"], "Wind Gust":["gust"], "Generation":["gust"]})
#     figs = wp.power_curve_hexbin(True)
#     figs[1].show()


