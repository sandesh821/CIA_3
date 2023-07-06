#Copyright (c) Microsoft. All rights reserved.
import requests
import pandas as pd
import numpy as np
from datetime import datetime  
from datetime import timedelta  
import importlib
import pywt
import pickle
from deepmc import models
#import models
from time import sleep
import glob
from pandas.tseries.offsets import DateOffset

#from azure.cosmosdb.table.tableservice import TableService
#from azure.cosmosdb.table.models import Entity, EntityProperty, EdmType

SENSOR_FEATURES = ['WindDirection', 'Temperature', 'WindSpeed']

def shift_index(ds_df, freq_minutes, num_indices):
    ds_df['datehour'] = ds_df.index.shift(-num_indices, freq=DateOffset(minutes=freq_minutes))
    ds_df = ds_df.reset_index(drop=True)
    ds_df = ds_df.set_index('datehour')
    return ds_df

# Extracts Forecast data and preprocess the data
def get_csv_ws_data(data_df, index='DateTime',frequency='60min'):
    data_df['index'] = pd.to_datetime(data_df['DateTime'])
    data_df['DateTime'] = data_df['index']
    data_df = data_df.assign(datehour=data_df['index'])
    data_df = data_df.reset_index(drop=True)
    data_df = data_df.set_index('DateTime')
    return data_df

def get_combined_data_ws_gs(start_time, frequency, sensor_id, location, only_forecast=False, station='DS', end_time=None):
    ts = datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%S") 
    
    if end_time is None:
        payload = {'key':'ee4702c60588349fae60b1e8e9fba658', 'gps':SENSOR_CONFIG[location+sensor_id]['GPS']}
        ds_forecast_df = get_weather_forecast_DS(payload, frequency=frequency)
        ds_forecast_df = ds_forecast_df
        ds_forecast_df = ds_forecast_df[['Precipitation', 'WindSpeed', 'Temperature', 'Humidity']]


        if only_forecast is False:
            if station=='DS':
                payload = {'key':'ee4702c60588349fae60b1e8e9fba658', 'gps':SENSOR_CONFIG[location+sensor_id]['GPS']}
                ds_df = get_weather_data_DS(payload,start_date=ts.strftime('%Y%m%d'), frequency=frequency)
            elif station=='NOAA CSV':
                payload = {'key':'ee4702c60588349fae60b1e8e9fba658', 'gps':SENSOR_CONFIG[location+sensor_id]['GPS'], 'state':SENSOR_CONFIG[location+sensor_id]['Province'], 'region':SENSOR_CONFIG[location+sensor_id]['NOAA Region']}
                ds_df = get_weather_data_noaacsv(payload,start_date=ts.strftime('%Y%m%d'), frequency=frequency)


            ds_df = ds_df[['Precipitation', 'WindSpeed', 'Temperature', 'Humidity']]
            ds_df = ds_df.append(ds_forecast_df)

        else:
            ds_df = ds_forecast_df
            
    else:                                     #if the end time is not None 
        if only_forecast is True:
            raise
        else:
            if station=='DS':
                payload = {'key':'ee4702c60588349fae60b1e8e9fba658', 'gps':SENSOR_CONFIG[location+sensor_id]['GPS']}
                ds_df = get_weather_data_DS(payload,start_date=ts.strftime('%Y%m%d'), end_date=end_time, frequency=frequency)
            elif station=='NOAA CSV':
                payload = {'key':'ee4702c60588349fae60b1e8e9fba658', 'gps':SENSOR_CONFIG[location+sensor_id]['GPS'], 'state':SENSOR_CONFIG[location+sensor_id]['Province'], 'region':SENSOR_CONFIG[location+sensor_id]['NOAA Region']}
                ds_df = get_weather_data_noaacsv(payload,start_date=ts.strftime('%Y%m%d'),end_date=end_time, frequency=frequency)
            else:
                ds_df = pd.DataFrame(columns=['Precipitation', 'WindSpeed', 'Temperature', 'Humidity'])


            ds_df = ds_df[['Precipitation', 'WindSpeed', 'Temperature', 'Humidity']]

    ds_df = shift_index(ds_df,frequency, 12)    

    start_time = ts - timedelta(hours=12*int(frequency))
    data_df = get_sensor_box_data(start_time.strftime("%Y-%m-%dT%H:%M:%S"),sensor_id=sensor_id,table=location,frequency=frequency)
    #Replace columns here
    data_df = data_df[['Precipitation', 'WindSpeed', 'Temperature', 'Humidity']]
    data_df = data_df.join(ds_df, how='inner',rsuffix='_forecast')
   

    data_df = data_df[['Precipitation', 'WindSpeed', 'Temperature', 'Humidity', 'Humidity_forecast']]

    if only_forecast is True:
        data_df = data_df[0:12]
        
    data_df = data_df.fillna(method='ffill')
    data_df = data_df.fillna(-1)

    return data_df


def convert_df_wavelet_training_set(data_df,n_pred_var, ts_lookback=12, ts_lookahead=12, validation = False, per_split=0.8):
    level = 5
    data_df = data_df[SENSOR_FEATURES]
    wavelet='bior2.2'
    wp5 = pywt.wavedec(data=data_df[n_pred_var], wavelet=wavelet, mode='periodic',level=level)
    rd = list()
    N = data_df.shape[0]
    for i in range(1,level+1):
        rd.append(pywt.waverec(wp5[:-i] + [None] * i, wavelet)[:N])
        
    with open('humidity_input_normalization_class', 'rb') as input_class_file:
        file_scaler = pickle.load(input_class_file)
    
    with open('humidity_output_normalization_class', 'rb') as output_class_file:
        t_scaler_y = pickle.load(output_class_file)
        
        
    t_scaler, scaler_y, t_train_X, train_y, t_test_X, test_y = models.dl_preprocess_data(data_df,ts_lookback=ts_lookback, ts_lookahead=ts_lookahead, pred_var_idx=[n_pred_var],validation=validation,scale_output_class=t_scaler_y,scale_input_class=file_scaler[0],per_split=per_split)



    wpt_df = data_df.copy()
    wpt_df = data_df.drop(n_pred_var, axis=1)
    scaler = list()
    train_X = list()
    test_X = list()

    scaler.append(t_scaler)
    train_X.append(t_train_X)
    test_X.append(t_test_X)
    idx=1
    for i in range(0,level):
        wpt_df[n_pred_var] = rd[i][:]
        wpt_df = wpt_df[SENSOR_FEATURES]
        
        t_scaler, _, t_train_X, _, t_test_X, _ = models.dl_preprocess_data(wpt_df,ts_lookback=ts_lookback, ts_lookahead=ts_lookahead, pred_var_idx=[n_pred_var],validation=validation,scale_output_class=t_scaler_y,scale_input_class=file_scaler[idx],per_split=per_split)

        scaler.append(t_scaler)
        train_X.append(t_train_X)
        test_X.append(t_test_X)
        idx = idx+1
        
    return scaler_y, train_X, train_y, test_X, test_y

def convert_df_wavelet_input(data_df,n_pred_var = 'WindSpeed'):
    level = 5
    data_df = data_df[SENSOR_FEATURES]
    
    wavelet = 'bior2.2'
    
    wp5 = pywt.wavedec(data=data_df[n_pred_var], wavelet=wavelet, mode='periodic',level=level)
    rd = list()
    N = data_df.shape[0]
    for i in range(1,level+1):
        rd.append(pywt.waverec(wp5[:-i] + [None] * i, wavelet)[:N])
        
    ts_lookback=24
    ts_lookahead=24
    with open('serialized/ws_input_normalization_class', 'rb') as input_class_file:
        file_scaler = pickle.load(input_class_file)
        
    t_scaler, _, t_train_X, _, t_test_X, _ = models.dl_preprocess_data(data_df,ts_lookback=ts_lookback,ts_lookahead=ts_lookahead,pred_var_idx=[n_pred_var],scale_input_class=file_scaler[0], validation=False, training=False)



    wpt_df = data_df.copy()
    wpt_df = data_df.drop(n_pred_var, axis=1)
    scaler = list()
    train_X = list()
    test_X = list()

    scaler.append(t_scaler)
    train_X.append(t_train_X)
    test_X.append(t_test_X)

    idx=1
    for i in range(0,level):
        wpt_df[n_pred_var] = rd[i][:]
        wpt_df = wpt_df[SENSOR_FEATURES]
        
        t_scaler, _, t_train_X, _, t_test_X, _ = models.dl_preprocess_data(wpt_df,ts_lookback=ts_lookback,ts_lookahead=ts_lookahead,pred_var_idx=[n_pred_var],scale_input_class=file_scaler[idx],validation=False, training=False)
        scaler.append(t_scaler)
        train_X.append(t_train_X)
        test_X.append(t_test_X)
        idx = idx+1
        
    with open('serialized/ws_output_normalization_class', 'rb') as output_class_file:
        scaler_y = pickle.load(output_class_file)     
        
    return scaler_y, train_X, None, test_X, None


def update_model(model, train_X, train_y, validation_data=None, server_mode=False):
    batch_size = 16
    # fit network
    history = model.fit(train_X, train_y, epochs=15, batch_size=batch_size, validation_data=validation_data,verbose=1)
    # plot history
    if server_mode is False:
        from matplotlib import pyplot as plt
        plt.plot(history.history['loss'], label='train')
        if validation_data is not None:
            plt.plot(history.history['val_loss'], label='test')
        #plt.plot(history.history['val_acc'], label='Accuracy')

        plt.legend()
        plt.show()
        
    return model


def get_sensor_names(farm,sensor_id):
    config = Get_Data_From_Azure_Table(credential_key=farm, table_name="AgSensorBoxConfig"+sensor_id)
    return pd.DataFrame(config)['FriendlyName'].tolist()


def get_weather_forecast_WA(payload, frequency='1'):
    #from weatherapi.com
    columns = ['WindDirection', 'Rain', 'WindSpeed', 'LocalTime', 'AmbientHumidity', 'Timestamp', 'AtmosphericPressure', 'AmbientTemperature', 'WindGust', 'CloudCover']
    data_df = pd.DataFrame(columns=columns)
    resp = requests.get('http://api.weatherapi.com/v1/forecast.json', params={'key':payload['key'], 'q':payload['gps'], 'days':payload['fs_days']} )
    while resp.status_code != 200:
        sleep(900)
        resp = requests.get('http://api.weatherapi.com/v1/forecast.json', params={'key':payload['key'], 'q':payload['gps'], 'days':payload['fs_days']} )
        
    data = list()
    for day in range(0,payload['fs_days']):
        for obs in resp.json()['forecast']['forecastday'][day]['hour']:
            data_dict = {}
            data_dict['Timestamp'] = datetime.fromtimestamp(float(obs['time_epoch']) ).strftime('%Y-%m-%d %H:%M')
            try:
                data_dict['Temperature'] = float(obs["temp_c"])
            except:
                data_dict['Temperature'] = None
            try:
                data_dict['Pressure'] = float(obs['pressure_in'])
            except:
                data_dict['Pressure'] = None
            try:
                data_dict['Humidity'] = float(obs['humidity'])
            except:
                data_dict['Humidity'] = None
            try:
                data_dict['WindSpeed'] = float(obs['wind_kph'])
            except:
                data_dict['WindSpeed'] = None
            try:
                data_dict['Precipitation'] = float(obs['precip_in'])
            except:
                data_dict['Precipitation'] = None
            try:
                data_dict['WindGust'] = float(obs['gust_kph'])
            except:
                data_dict['WindGust'] = None
            try:
                data_dict['CloudCover'] = float(obs['cloud'])
            except:
                data_dict['CloudCover'] = None
            try:
                data_dict['WindDirection'] = float(obs['wind_degree'])
            except KeyError:
                data_dict['WindDirection'] = None
            data.append(data_dict)
    
    data_df = pd.DataFrame(data)
    data_df['Timestamp'] = pd.to_datetime(data_df['Timestamp'])
    
    #data_df['Timestamp'] = convert_tz_local_utc(data_df['Timestamp'],resp.json()['timezone'])
    
    data_df = data_df.assign(
       datehour=pd.to_datetime(data_df.Timestamp.dt.date) +
            pd.to_timedelta(data_df.Timestamp.dt.hour, unit='H'))
    data_df = data_df.reset_index(drop=True)
    data_df = data_df.set_index('datehour')
    
    data_df = data_df.groupby(pd.Grouper(freq=frequency + 'H')).mean()
    #for key, values in data_df.iteritems():
    #    for idx, value in values.items():
    #        if np.isnan(value):
    #            try:
    #                data_df.loc[idx, key] = data_df.loc[idx- pd.to_timedelta(1, unit='d'), key]
    #            except KeyError:
    #                data_df.loc[idx, key] = float(data_df.mean(axis=0)[key])
    #data_df["Current Hour"] = data_df.apply (lambda row: row.name.hour - 12., axis=1)
    #data_df["Days since SOY"] = data_df.apply(lambda row: n_days_soy(row), axis=1)
    
    return data_df


def get_weather_data_WA(payload, start_date, end_date=None, frequency='1'):
    #weatherapi.com
    if end_date is None:
        end_date = datetime.now().date()
    else:
        end_date = datetime.strptime(end_date, '%Y%m%d').date() + timedelta(days=1)
    date = datetime.strptime(start_date, '%Y%m%d').date() - timedelta(days=1)
    ## Check if needed######
    columns = ['Wind Direction', 'Rain', 'WindSpeed', 'LocalTime', 'Ambient Humidity', 'Timestamp', 'Atmospheric Pressure', 'Ambient Temperature', 'Wind Gust', 'Cloud Cover']
    data_df = pd.DataFrame(columns=columns)
    ########################
    
    
    data = list()
    while date <= end_date:
        payload['date'] = datetime.strftime(date,'%Y-%m-%d')
        print(payload['date'])
        resp = requests.get('http://api.weatherapi.com/v1/history.json', params={'key':payload['key'], 'q':payload['gps'], 'dt':payload['date']} )
        date = date + timedelta(days=1)
        if resp.status_code != 200:
            # This means something went wrong.
            continue
        
        for obs in resp.json()['forecast']['forecastday']['hour']:
            data_dict = {}
            data_dict['Timestamp'] = datetime.fromtimestamp(obs['time'] ).strftime('%Y-%m-%d %H:%M')
            try:
                data_dict['Temperature'] = obs["temp_c"]
            except:
                data_dict['Temperature'] = None
            try:
                data_dict['Pressure'] = obs['pressure_in']
            except:
                data_dict['Pressure'] = None
            try:
                data_dict['Humidity'] = obs['humidity']
            except:
                data_dict['Humidity'] = None
            try:
                data_dict['WindSpeed'] = obs['wind_kph']
            except:
                data_dict['WindSpeed'] = None
            try:
                data_dict['Precipitation'] = float(obs['precip_in'])
            except:
                data_dict['Precipitation'] = None
            try:
                data_dict['WindGust'] = float(obs['gust_kph'])
            except:
                data_dict['WindGust'] = None
            try:
                data_dict['CloudCover'] = float(obs['cloud'])
            except:
                data_dict['CloudCover'] = None
            try:
                data_dict['WindDirection'] = obs['wind_degree']
            except KeyError:
                data_dict['WindDirection'] = None
            data.append(data_dict)
    
    data_df = pd.DataFrame(data)
    data_df['Timestamp'] = pd.to_datetime(data_df['Timestamp'])
    #data_df['Timestamp'] = convert_tz_local_utc(data_df['Timestamp'],resp.json()['timezone'])
        
        
    data_df = data_df.assign(
       datehour=pd.to_datetime(data_df.Timestamp.dt.date) +
            pd.to_timedelta(data_df.Timestamp.dt.hour, unit='H'))
    data_df = data_df.reset_index(drop=True)
    data_df = data_df.set_index('datehour')
    data_df = data_df.groupby(pd.Grouper(freq=frequency + 'H')).mean()
    #for key, values in data_df.iteritems():
    #    for idx, value in values.items():
    #        if np.isnan(value):
    #            try:
    #                data_df.loc[idx, key] = data_df.loc[idx- pd.to_timedelta(1, unit='d'), key]
    #            except KeyError:
    #                data_df.loc[idx, key] = float(data_df.mean(axis=0)[key])
    #data_df["Current Hour"] = data_df.apply (lambda row: row.name.hour - 12., axis=1)
    #data_df["Days since SOY"] = data_df.apply(lambda row: n_days_soy(row), axis=1)
    
    return data_df

def convert_tz_local_utc(timestamp_ds,timezone):
    try:
        timestamp_ds = timestamp_ds.dt.tz_localize(timezone, ambiguous='infer').dt.tz_convert('UTC')
    except:
        timestamp_ds = timestamp_ds.dt.tz_localize(timezone, ambiguous=True).dt.tz_convert('UTC')
        
    return timestamp_ds
    
def get_weather_data_noaacsv(payload,start_date=None, end_date=None, frequency='1'):
    ds_df = get_weather_data_DS(payload, start_date=start_date, end_date=end_date, frequency=frequency)
    
    if end_date is None:
        end_date = datetime.now().date()
    else:
        end_date = datetime.strptime(end_date, '%Y%m%d').date() + timedelta(days=2)
    
    start_date = datetime.strptime(start_date, '%Y%m%d').date() - timedelta(days=1)
    
    path = 'soil01/' + 'SOIL01_' + payload['state'] +'_' + payload['region'] + '*.csv'
    for file in glob.glob(path):
        data_df = pd.read_csv(file)
        
    index = 'UTC_DATETIME'
    data_df[index] = pd.to_datetime(data_df[index],format='%Y%m%d%H')
    
    data_df = data_df.assign(
        datehour=pd.to_datetime(data_df[index].dt.date) +
             pd.to_timedelta(data_df[index].dt.hour, unit='H'))
    
    if start_date is not None and end_date is not None:
        mask = (data_df['datehour'] > start_date) & (data_df['datehour'] <= end_date)
    
        data_df = data_df.loc[mask]
        
        
    data_df = data_df.reset_index(drop=True)
    data_df = data_df.set_index('datehour')
        
    data_df = data_df.groupby(pd.Grouper(freq=frequency + 'H')).mean()
    data_df['Temperature'] = data_df['T_HR_AVG']
    data_df['Precipitation']=data_df['P_OFFICIAL']
    data_df['WindSpeed']=data_df['WINDSPD']
    data_df = data_df[['Precipitation', 'WindSpeed', 'Temperature']]
    data_df = data_df.groupby(pd.Grouper(freq=frequency + 'H')).mean()
    
     
    ds_df = ds_df['Humidity']
    
    data_df = data_df.join(ds_df, how='outer')
    data_df.drop(data_df.tail(1).index,inplace=True)
    data_df.drop(data_df.head(1).index,inplace=True)
    
    return data_df




def tseries_to_output(tseries, ts=24):
    output = list()
    for idx in range(0,len(tseries)-ts):
        output.append(tseries[idx:idx+ts].T[0])
    return output

def ticks(time_stamp: datetime):
    return int((time_stamp - datetime(1, 1, 1)).total_seconds() * 10000000)

def n_days_soy(row):
    year = row.name.year
    days = row.name - pd.Timestamp(str(year) + "-01-01")
    return days.days


def Get_Data_From_Azure_Table(account_name:str, credential_key:str, table_name:str, query_filter:str=""):
    result = []
    next_marker = {}
    
    while True:
        table_service = TableService(account_name=account_name, account_key=credential_key)
        data = table_service.query_entities(table_name, filter=query_filter, marker=next_marker)
        result.extend(data.items)
        
        if(bool(data.next_marker)):
            next_marker = data.next_marker
        else:
            break
        
    return result


# In[4]:


def get_sensor_box_data(time_stamp_str,sensor_id,table,frequency="1"):
    table_service = TableService(account_name=SENSOR_CONFIG[table+sensor_id]['ACCOUNT_NAME'], account_key=SENSOR_CONFIG[table+sensor_id]['KEY'])    

    data = Get_Data_From_Azure_Table(SENSOR_CONFIG[table+sensor_id]['ACCOUNT_NAME'], SENSOR_CONFIG[table+sensor_id]['KEY'],  'AgSensorBoxData' + sensor_id, "PartitionKey eq 'FarmName' and Timestamp gt datetime'" + time_stamp_str + "'")
    
    
    schema = Get_Data_From_Azure_Table(SENSOR_CONFIG[table+sensor_id]['ACCOUNT_NAME'], SENSOR_CONFIG[table+sensor_id]['KEY'], 'AgSensorBoxConfig' + sensor_id)
    channel_mapping = {}

    schema_df = pd.DataFrame(schema)
    for index, row in schema_df.iterrows():
        try:
            label = SENSOR_CONFIG[table+sensor_id]['NAME_MAPPINGS'][row.FriendlyName]
            channel_mapping["CompChannel" + str(row.RowKey)] = label
        except KeyError:
            continue
    
    data_df = pd.DataFrame(data)
    data_df = data_df.rename(columns=channel_mapping)
    data_df['Timestamp'] = pd.to_datetime(data_df['Timestamp'])
    data_df = data_df.assign(
        datehour=pd.to_datetime(data_df.Timestamp.dt.date) +
             pd.to_timedelta(data_df.Timestamp.dt.hour, unit='H'))
    
    #todo: generalize this
    columns = list(channel_mapping.values())
    columns.append('datehour')
    try:
        columns.remove('BME280 Temperature')
    except ValueError:
        pass
    try:
        columns.remove('BME280 Humidity')
    except ValueError:
        pass
    try:
        columns.remove('BME280 Pressure')
    except ValueError:
        pass
    try:
        columns.remove('Battery Level')
    except ValueError:
        pass
    try:
        columns.remove('BatteryVoltage')
    except ValueError:
        pass
#     try:
#         columns.remove('Soil Moisture')
#     except ValueError:
#         pass
#     try:
#         columns.remove('Soil Temperature')
#     except ValueError:
#         pass
    try:
        columns.remove('CO2')
    except ValueError:
        pass
    data_df = data_df[columns]
    data_df = data_df.reset_index(drop=True)
    data_df = data_df.set_index('datehour')
    data_df = data_df.groupby(pd.Grouper(freq=frequency + 'H')).mean()
    for key, values in data_df.iteritems():
        for idx, value in values.items():
            if np.isnan(value):
                data_df.loc[idx, key] = data_df.loc[idx- pd.to_timedelta(1, unit='d'), key]
                
    #data_df["Current Hour"] = data_df.apply (lambda row: row.name.hour - 12., axis=1)
    #data_df["Days since SOY"] = data_df.apply(lambda row: n_days_soy(row), axis=1)
        
    
    return data_df


def rename_sensor_df(data_df):
    for column in data_df.columns:
        if data_df[column].max() == data_df[column].min():
            data_df = data_df.drop(columns=[column])
            continue
        for feature in SENSOR_FEATURES:
            if feature in column:
                data_df = data_df.rename(columns={column: feature})
                break
    return data_df

def get_csv_data(path='darksky20170501.csv',station='',index='Timestamp', sep=','):
    
    data_df = pd.read_csv(path, sep=sep, index_col=False)
    data_df[index] = pd.to_datetime(data_df[index])
    
    data_df = data_df.assign(
        datehour=pd.to_datetime(data_df[index].dt.date) +
             pd.to_timedelta(data_df[index].dt.hour, unit='H'))
    data_df = data_df.reset_index(drop=True)
    data_df = data_df.set_index('datehour')
    
    if(station != ''):
        data_df = data_df[data_df.station==station]
        data_df = data_df.drop(['station','Unnamed: 0'],axis=1)
    
    return data_df

def get_csv_ws_data(path,index='DateTime',frequency='60min', format=None, sep=',', dtype={}):
    
    data_df = pd.read_csv(path,sep=sep, index_col=False, dtype=dtype)
    data_df[index] = pd.to_datetime(data_df[index],format=format)
    
    data_df = data_df.assign(datehour=data_df[index])
    data_df = data_df.reset_index(drop=True)
    data_df = data_df.set_index('datehour')
    data_df['Temperature'] = data_df['AmbientTemperature']
    #data_df['Humidity']=data_df['RelativeHumidity']
    data_df['WindSpeed']=data_df['WindSpeed']
    data_df['WindDirection']=data_df['WindDirection']
    #data_df['WindSpeed_RollingMean']=data_df['WindSpeed_RollingMean']
    
    data_df = data_df[SENSOR_FEATURES]
#     for key, values in data_df.iteritems():
#         for idx, value in values.items():
#             if np.isnan(value):
#                 data_df.loc[idx, key] = data_df.loc[idx- pd.to_timedelta(1, unit='m'), key]
    
    data_df = data_df.interpolate(method='from_derivatives')
    #data_df = data_df.fillna(method='bfill')
    data_df = data_df.groupby(pd.Grouper(freq=frequency)).mean()
    data_df = data_df.interpolate(method='from_derivatives')
#     data_df = data_df.fillna(method='ffill')
#     data_df = data_df.fillna(method='bfill')
    
    return data_df

def get_csv_we_data(path='data/ws_data.csv',index='DateTime',frequency='60min'):
    
    data_df = pd.read_csv(path)
    data_df[index] = pd.to_datetime(data_df[index])
    
    data_df = data_df.assign(datehour=data_df[index])
    data_df = data_df.reset_index(drop=True)
    data_df = data_df.set_index('datehour')
    data_df['Temperature'] = data_df['ATMP(degC)']
    data_df['Humidity']=data_df['HUMD(per)']
    data_df['Radiation']=data_df['TILT(Wpm2)']
    data_df['MTemperature']=data_df['MTMP(degC)']
    data_df['CloudOpacity']=data_df['CloudOpacity']
    data_df['Power']=data_df['Power']
    #data_df['WindSpeed_RollingMean']=data_df['WindSpeed_RollingMean']
    
#    data_df = data_df[['WindEnergy']]
#     for key, values in data_df.iteritems():
#         for idx, value in values.items():
#             if np.isnan(value):
#                 data_df.loc[idx, key] = data_df.loc[idx- pd.to_timedelta(1, unit='m'), key]
    
    data_df = data_df.fillna(method='ffill')
    data_df = data_df.fillna(method='bfill')
    #data_df = data_df.fillna(method='bfill')
    data_df = data_df.groupby(pd.Grouper(freq=frequency)).mean()
    data_df = data_df.fillna(method='ffill')
    data_df = data_df.fillna(method='bfill')
    
    return data_df
