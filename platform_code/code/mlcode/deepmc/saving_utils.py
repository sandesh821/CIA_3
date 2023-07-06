import warnings
warnings.filterwarnings('ignore')
import os
import pandas as pd
import ast
import glob
from math import sqrt

from matplotlib.dates import DateFormatter
import matplotlib.dates as mdates

import matplotlib.pyplot as plt
import seaborn as sns; sns.set()

from scipy.stats import norm
import lightgbm as lgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_log_error
from sklearn import preprocessing
from sklearn.model_selection import cross_val_score, cross_val_predict
from sklearn.metrics import mean_squared_error

import numpy as np
import matplotlib.pyplot as plt
import copy
from pathlib import Path
import warnings

Plant_Capacity = 50
PPA = 2.91
deviation_gap = 10 
#8 for only GJ 

def get_deviation_0(Regulation):
    if Regulation in ['CERC','KA', 'UP','MH', 'RJ', 'AP'] : 
            return 15
    elif Regulation in ['MP', 'TN', 'HR'] : 
            return 10
    elif Regulation in ['GJ'] : return 7
            
def get_deviation_1(Regulation):
    if Regulation in ['CERC','KA', 'UP','MH', 'RJ', 'AP']: return 25
    elif Regulation in ['MP', 'TN', 'HR']: return 20
    elif Regulation in ['GJ']: return 15
                    
def get_deviation_2(Regulation): 
    if Regulation in ['CERC','KA', 'UP','MH', 'RJ', 'AP']: return 35
    elif Regulation in ['MP', 'TN', 'HR']: return 30
    elif Regulation in ['GJ']: return 23

def get_penalty_rate_slab1(Regulation):
    if Regulation in ['CERC']:
            return PPA*0.1
    elif Regulation in ['KA', 'UP','MH', 'RJ', 'AP','MP', 'TN', 'HR'] : 
            return 0.5
    elif Regulation in ['GJ'] : return 0.25
    
def get_penalty_rate_slab2(Regulation):
    if Regulation in ['CERC']:
            return PPA*0.2
    elif Regulation in ['KA', 'UP','MH', 'RJ', 'AP','MP', 'TN', 'HR'] : 
            return 1
    elif Regulation in ['GJ'] : return 0.5

def get_penalty_rate_slab3(Regulation):
    if Regulation in ['CERC']:
            return PPA*0.3
    elif Regulation in ['KA', 'UP','MH', 'RJ', 'AP','MP', 'TN', 'HR'] : 
            return 1.5
    elif Regulation in ['GJ'] : return 0.75
    
    
def get_slab(deviation,deviation_slab0,deviation_slab1,deviation_slab2):
    if deviation <= deviation_slab0:
        return 0
    elif deviation_slab0 < deviation <= deviation_slab1:
        return 1
    elif deviation_slab1 < deviation <= deviation_slab2:
        return 2
    elif deviation > deviation_slab2:
        return 3
    
def energy_deviation_slab1(row,deviation_slab0):
    if row["Slab"] == 0:
        return 0
    elif row["Slab"] == 1:
        return row["Shortfall"] - (Plant_Capacity*250*deviation_slab0/100)
    elif row["Slab"] > 1:
        return Plant_Capacity*250*deviation_gap/100
    
def energy_deviation_slab2(row,deviation_slab1):
    if row["Slab"] == 2:
        return row["Shortfall"] - (Plant_Capacity*250*deviation_slab1/100)
    elif row["Slab"] > 1:
        return Plant_Capacity*250*deviation_gap/100
    else:
        return 0

def energy_deviation_slab3(row,deviation_slab2):
    if row["Slab"] == 3:
        return row["Shortfall"] - (Plant_Capacity*250*deviation_slab2/100)
    else:
        return 0
    
def compute_penalties(df, forecast_col, Regulation):
    

# KA is Karnataka,  UP is Uttar Pradesh, MH is Maharastra, RJ is Rajasthan, GJ is Gujarat
# MP is MadhyaPradesh, TN is Tamil Nadu, AP is Andhra PRadesh, HR is Haryana
# CERC is CERC Inter State DSM Regulation

    
    df["Error"] = np.abs(df[forecast_col]-df["Actual Generation"])/Plant_Capacity*100
    
    deviation_slab0 = get_deviation_0(Regulation)
    deviation_slab1 = get_deviation_1(Regulation)
    deviation_slab2 = get_deviation_2(Regulation)

    
    df["Slab"] = df["Error"].apply(get_slab, args=(deviation_slab0,deviation_slab1,deviation_slab2))

    df["Shortfall"] = np.abs(df[forecast_col]-df["Actual Generation"])*1000/4.

    df["Deviated Energy_slab1"] = df.apply(energy_deviation_slab1, args=(deviation_slab0, ), axis=1)
    df["Deviated Energy_slab2"] = df.apply(energy_deviation_slab2, args=(deviation_slab1, ), axis=1)
    df["Deviated Energy_slab3"] = df.apply(energy_deviation_slab3, args=(deviation_slab2, ), axis=1)
    
    Deviated_Energy_slab1 = df[["Deviated Energy_slab1"]].sum(axis=0)[0]
    Deviated_Energy_slab2 = df[["Deviated Energy_slab2"]].sum(axis=0)[0]
    Deviated_Energy_slab3 = df[["Deviated Energy_slab3"]].sum(axis=0)[0]

    Penalty_rate_slab1 = get_penalty_rate_slab1(Regulation)
    Penalty_rate_slab2 = get_penalty_rate_slab2(Regulation)
    Penalty_rate_slab3 = get_penalty_rate_slab3(Regulation)
    
    Penalty_slab1 = Deviated_Energy_slab1*Penalty_rate_slab1
    Penalty_slab2 = Deviated_Energy_slab2*Penalty_rate_slab2
    Penalty_slab3 = Deviated_Energy_slab3*Penalty_rate_slab3

    Total_Penalty = Penalty_slab1 + Penalty_slab2 + Penalty_slab3
    return df, Deviated_Energy_slab1,Penalty_slab1,Total_Penalty


import numpy as np

def nrmse(y_true, y_pred):
    mu = np.mean(y_true)
#     print("Average value:", mu)
    if mu != 0:
        return mean_squared_error(y_pred, y_true) ** 0.5 / mu
    else:
        return 0
    
def accuracy_matrix(forecast, actual):
    mape = np.mean(np.abs(forecast - actual)/np.abs(actual))  # MAPE
    me = np.mean(forecast - actual)             # ME
    mae = np.mean(np.abs(forecast - actual))    # MAE
    mpe = np.mean((forecast - actual)/actual)   # MPE
    rmse = np.mean((forecast - actual)**2)**.5  # RMSE
    corr = np.corrcoef(forecast, actual)[0,1]   # corr
    mins = np.amin(np.hstack([forecast[:,None],actual[:,None]]), axis=1)
    maxs = np.amax(np.hstack([forecast[:,None],actual[:,None]]), axis=1)
#     print(f"\nME = {me :.2f} \nRMSE = {rmse :.2f} \nCORR = {corr :.2f} ")
    return me, corr


def get_daily_rmse(df, model_name):
    rmse_model, rmse_ayana = [], []
    for i in range(1, len(df['DateTime'].dt.date.unique())+1):
        temp = df[df['DateTime'].dt.day == i]
        rmse_model.append(np.mean((temp['Forecast_' + model_name] - temp['Actual Generation'])**2)**.5)  # RMSE
        rmse_ayana.append(np.mean((temp['Forecast_ayana'] - temp['Actual Generation'])**2)**.5)  # RMSE
    return rmse_model, rmse_ayana

def get_error(df_joined, model_name):
    df_joined['Error_ayana'] = df_joined['Forecast_ayana'] - df_joined['Actual Generation']
    df_joined['Error_' + str(model_name)] = df_joined['Forecast_' + str(model_name)] - df_joined['Actual Generation']
    num_days = 7
    num_steps = num_days * 24 * 4
    date_form = DateFormatter("%d-%m-%y")
    a4_dims = (12, 8.5)
    fig, ax = plt.subplots(figsize=a4_dims)
    # df_joined_apr['DateTime'] = pd.to_datetime(df_joined_apr['DateTime'])
    g1 = sns.lineplot(x='DateTime',
    y='value',
    hue='variable',
    data=pd.melt(df_joined[:num_days * 24 * 4][["DateTime", "Error_" + str(model_name), "Error_ayana"]],
    ['DateTime']))
    g1.xaxis.set_major_formatter(date_form)
    g1.xaxis.set_major_locator(mdates.DayLocator(interval=1))

    
# Compare TFT results with Ayana results
def compare_with_ayana(results, model_name, path):
    import pandas as pd
    def join_date_time(row):
        return str(row['Date']) + ' ' + str(row['FROM TIME'])
    
    power_data = pd.ExcelFile(path,engine='openpyxl') #Block2 is Ady2
    power_data.sheet_names

    power_data = pd.read_excel(path, 'Calculation Sheet')
    power_data = power_data.iloc[1:]

    power_data['DateTime'] = power_data.apply(join_date_time, axis=1)
    power_data['DateTime'] = pd.to_datetime(power_data['DateTime'])
    df_joined = results.merge(power_data, on="DateTime", how="inner", suffixes=("_" + model_name, "_ayana"))
    df_joined = df_joined[['DateTime', 'Forecast_' + model_name, 'Forecast_ayana', 'Actual Generation']]
    df_joined.dropna(inplace=True)
    
    date_list = []
    date_list = pd.to_datetime(date_list)
    df_joined = df_joined[~df_joined['DateTime'].dt.normalize().isin(date_list)]

    df_joined['Hour'] = df_joined['DateTime'].dt.hour
    df_joined['DateTime'] = pd.to_datetime(df_joined['DateTime'])

    df_joined.loc[df_joined['Hour'] >= 19, 'Forecast_' + model_name] = 0
    df_joined.loc[df_joined['Hour'] < 5, 'Forecast_' + model_name] = 0

    num1 = 1
    num2 = 7
    
    start = num1 * 24 * 4
    end = num2 * 24 * 4

    date_form = DateFormatter("%d-%m-%y")
    a4_dims = (15, 5)
    fig, ax = plt.subplots(figsize=a4_dims)
    g1 = sns.lineplot(x='DateTime',
                 y='value',
                 hue='variable', 
                 data=pd.melt(df_joined[:end][["DateTime", 'Forecast_' + model_name, "Actual Generation"]],
                              ['DateTime']))
    g1.xaxis.set_major_formatter(date_form)
    g1.xaxis.set_major_locator(mdates.DayLocator(interval=1))
    plt.ylabel('Power')
    plt.title("Power Comparison");
    
    get_error(df_joined, model_name)
    
    return df_joined

def calculate_savings(how, df_joined, model_name):
    count = 1
    my_dict = {}
    
    if how == "Daily":
        grouped = df_joined.groupby(pd.Grouper(key='DateTime', axis=0, freq='1D'))
        final_count = 31
        
    elif how == "Weekly":
        grouped = df_joined.groupby(pd.Grouper(key='DateTime', axis=0, freq='7D'))
        final_count = 5

    for group_name, df_group in grouped:
        if count > final_count:
            count=1
        forecast = df_group['Forecast_' + model_name]
        actual = df_group['Actual Generation']

        rmse_model = round(mean_squared_error(df_group['Forecast_' + model_name], df_group['Actual Generation']) ** 0.5, 5)
        nrmse_model = round(nrmse(df_group['Actual Generation'], df_group['Forecast_' + model_name]), 5)

        rmse_ayana = round(mean_squared_error(df_group['Forecast_ayana'], df_group['Actual Generation']) ** 0.5, 5)
        nrmse_ayana = round(nrmse(df_group['Actual Generation'], df_group['Forecast_ayana']), 5)

        me, corr = accuracy_matrix(forecast, actual)
        
        df_deepmc, DE_slab1_deepmc, Penalty_slab1_deepmc, Total_Penalty_deepmc = compute_penalties(df_group, "Forecast_" + model_name, "CERC")
        
        df_ayana,DE_slab1_ayana, Penalty_slab1_ayana, Total_Penalty_ayana = compute_penalties(df_group, "Forecast_ayana", "CERC")
        
        saving = Total_Penalty_ayana - Total_Penalty_deepmc

        my_dict[how[0] + "_" + str(count)] = {how + '_RMSE':rmse_model, 
                           how + '_NRMSE': nrmse_model,
                           how + "_RMSE_Ayana": rmse_ayana,
                           how + "_NRMSE_Ayana": nrmse_ayana,
                           how + "_ME": me,
                           how + "_Corr":corr,
                           how + "_Saving": saving}
        count+=1
        if count > 10:
            break
        
    RMSE =  round(mean_squared_error(df_joined['Forecast_' + model_name], df_joined['Actual Generation']) ** 0.5, 5)
    NRMSE =round(nrmse(df_joined['Actual Generation'], df_joined['Forecast_' + model_name]), 5)

    Ayana_RMSE = round(mean_squared_error(df_joined['Forecast_ayana'], df_joined['Actual Generation']) ** 0.5, 5)
    Ayana_NRMSE= round(nrmse(df_joined['Actual Generation'], df_joined['Forecast_ayana']), 5)
    
    df_deepmc, DE_slab1_deepmc, Penalty_slab1_deepmc, Total_Penalty_deepmc = compute_penalties(df_joined, "Forecast_" + model_name, "CERC")

    df_ayana,DE_slab1_ayana, Penalty_slab1_ayana, Total_Penalty_ayana = compute_penalties(df_joined, "Forecast_ayana", "CERC")

    saving = Total_Penalty_ayana - Total_Penalty_deepmc
    me, corr = accuracy_matrix(df_joined["Forecast_" + model_name], df_joined["Actual Generation"])
    
    daily_rmse_model, daily_rmse_ayana = get_daily_rmse(df_joined, model_name)
#     print("daily_rmse_model :: ", len(daily_rmse_model))
    
    my_dict['Month'] = {'RMSE':RMSE, 
                       'NRMSE': NRMSE,
                       "RMSE_Ayana": Ayana_RMSE,
                       "NRMSE_Ayana": Ayana_NRMSE,
                       "ME": me,
                       "Corr":corr,
                       "Saving": saving}
    
    
    x1 = pd.DataFrame(my_dict)
    y1 = x1["RMSE":"Saving"]['Month'].values
    x1.drop(columns=['Month'], inplace=True)
    x1.dropna(inplace=True)
    x1['Total_Monthly_Result'] = y1
    
    return x1

def get_savings(df_joined, model_name, dates):

    daily_rmse_model, daily_rmse_ayana = get_daily_rmse(df_joined, model_name)

    daily_savings = calculate_savings(how="Daily", df_joined=df_joined, model_name=model_name)
    
    weekly_savings = calculate_savings(how="Weekly", df_joined=df_joined, model_name=model_name)
    
    dates = pd.DataFrame({"DateTime" : pd.to_datetime(pd.date_range(start=dates.min().date(),end=dates.max().date()))})
    plt.figure(figsize=(8,4))
    sns.lineplot(dates["DateTime"], daily_rmse_model, label=model_name)
    sns.lineplot(dates["DateTime"], daily_rmse_ayana,label="Ayana")
    plt.ylabel("RMSE")
    plt.xticks(rotation=10);
    plt.title("Daily RMSE Comparison");
  
    return daily_savings, weekly_savings, daily_rmse_model, daily_rmse_ayana