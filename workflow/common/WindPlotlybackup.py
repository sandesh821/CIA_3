#Copyright (c) Microsoft. All rights reserved.
from UnivariatePlotly import UnivariatePlotly
from MultivariatePlotly import MultivariatePlotly
import plotly.express as px

class WindPlotly(UnivariatePlotly, MultivariatePlotly):
    def __init__(self, df, windspeed_cols_dict, winddirection_cols_dict):
        pass

    def wind_rose(self, windspeed_col, winddirection_col):
        fig = px.bar_polar(self.df, r="frequency", theta=winddirection_col,
                           color="strength", template="plotly_dark",
                           color_discrete_sequence=px.colors.sequential.Plasma_r)
        return fig

    def power_curve_implied(self):
        pass

    def power_curve_box(self, theoretical=True):
        pass

    def power_curve_scatter(self):
        pass

