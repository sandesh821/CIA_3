#Copyright (c) Microsoft. All rights reserved.
import plotly.express as px
import plotly.figure_factory as ff
import pandas as pd

class UnivariatePlotly:
    def __init__(self, df, column, index, tags=None):
        self.df = df
        self.column = column
        self.index = index
        self.tags = tags

    def _data_selector(self, start_date=None, end_date=None):
        df_local = self.df
        if start_date is not None:
            df_local = df_local[df_local[self.index] >= start_date]
        if end_date is not None:
            df_local = df_local[df_local[self.index] <= end_date]
        return df_local

    def cdf_graph(self, marginal="rug", start_date=None, end_date=None): #marginal = rug, violin, box
        df_local = self.df
        if start_date is not None and end_date is not None:
            df_local = self._data_selector(start_date=start_date, end_date=end_date)

        return px.ecdf(df_local, x=self.column, marginal=marginal)

    def pdf_graph(self, start_date=None, end_date=None):
        df_local = self.df
        if start_date is not None and end_date is not None:
            df_local = self._data_selector(start_date=start_date, end_date=end_date)

        return ff.create_distplot([df_local[self.column].tolist()], [self.column])#, bin_size=args['bin_size'], show_rug=args['show_rug'])

    def line_graph(self):
        fig = px.line(self.df, x=self.index, y=self.column)
        fig.update_xaxes(rangeslider_visible=True,
                         rangeselector=dict(buttons=list([
            dict(count=1, label="1m", step="month", stepmode="backward"),
            dict(count=6, label="6m", step="month", stepmode="backward"),
            dict(count=1, label="YTD", step="year", stepmode="todate"),
            dict(count=1, label="1y", step="year", stepmode="backward"),
            dict(step="all")
        ])))
        return fig

    def boxplot_graph(self, start_date=None, end_date=None):
        df_local = self.df
        if start_date is not None and end_date is not None:
            df_local = self._data_selector(start_date=start_date, end_date=end_date)

        figs = {}
        for tag in self.tags:
            figs[tag] = px.box(df_local, x=tag, y=self.column, title=tag)
        return figs


def reader():
    df = pd.read_csv("AAPL.csv", parse_dates=True, index_col="Date")
    df['Year'] = df.index.year
    df['Month'] = df.index.month
    df['Date'] = df.index
    return df

if __name__ == '__main__':
    df = reader()
    up = UnivariatePlotly(df, "Open", "Date", ['Year','Month'])

    fig = up.cdf_graph()
    fig.show()

    fig = up.pdf_graph()
    fig.show()

    fig = up.line_graph()
    fig.show()

    figs = up.boxplot_graph()
    for _, fig in figs.items():
        fig.show()