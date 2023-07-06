#Copyright (c) Microsoft. All rights reserved.
import datetime
from datetime import datetime,timedelta
import numpy as np

def extract_hour(df,new_col):
    df[new_col] = df['DateTime'].dt.hour
    return df

def extract_day(df,new_col):
    df[new_col] = df['DateTime'].dt.day
    return df

def extract_sin(df,col,new_col):
    df[new_col] = np.sin(df[col])
    return df

def extract_cos(df,col,new_col):
    df[new_col] = np.cos(df[col])
    return df

# def add(df,new_col):
#     df[new_col] = df['power']*1000
#     return df

# def divide(df,new_col):
#     df[new_col] = df['power']/1000
#     return df
