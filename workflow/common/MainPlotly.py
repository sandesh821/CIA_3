#Copyright (c) Microsoft. All rights reserved.
class MainPlotly:

    @classmethod
    def _clean_cols(cls, sel_cols, all_cols):
        if sel_cols is None:
            sel_cols = all_cols
        return sel_cols

    @classmethod
    def _data_selector(cls, df, index, start_date=None, end_date=None):
        df_local = df
        if start_date is not None:
            df_local = df_local[df_local[index] >= start_date]
        if end_date is not None:
            df_local = df_local[df_local[index] <= end_date]
        return df_local