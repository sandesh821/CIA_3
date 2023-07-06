#Copyright (c) Microsoft. All rights reserved.
import pandas as pd
from datetime import datetime, timedelta

def __init__():
    pass

def dropDuplicates(data,subsetCoulmn):
    data = data.drop_duplicates(subset=subsetCoulmn)
    return data

def fillMissingValues(data,freq,blocks,dateField = 'DateTime'):
    data[dateField] = pd.to_datetime(data[dateField])
    start = data[dateField].dt.date.min()
    end = data[dateField].dt.date.max() + timedelta(days=1)

    dates = pd.DataFrame({dateField:pd.to_datetime(pd.date_range(start=start, end=end, freq=freq)[:-1])})

    data = pd.merge(data, dates, on=dateField, how='right')
    data.ffill(inplace=True)
    data.bfill(inplace=True)
        # Can use interpolation as well here

    data['Month'] = data[dateField].dt.month
    data['Day'] = data[dateField].dt.day
    data['Hour'] = data[dateField].dt.hour

    data['Year'] = data[dateField].dt.year 
    data['Group'] = ["grp"] * len(data)
    b = [i for i in range(0, blocks)] * round(len(data) / blocks)
    data['Block'] = b[:len(data)]
    data["time_idx"] = data.index

    return data

def convert_to_string(train):
    train['Month'] = train['Month'].astype(str)
    train['Day'] = train['Day'].astype(str)
    train['Hour'] = train['Hour'].astype(str)
    train['Block'] = train['Block'].astype(str)
    train['Year'] = train['Year'].astype(str)

    train.reset_index(inplace=True)
    return train

def get_val(df_power2):
    dates, preds = [], []
    count = 0
    for index, row in df_power2.iterrows():
        if index % 6 == 0:
            all_preds = [row['P_'+str(ii)] for ii in range(9)]
            preds.extend(all_preds[3:])
            count += 1
    return preds