#Copyright (c) Microsoft. All rights reserved.
import pandas as pd
import numpy as np
from datetime import datetime  
from datetime import timedelta  
import modules
from matplotlib import pyplot as plt
from keras.models import load_model

def online_test(farm, sensor_id, predictor, ts_lookahead=12):
    data_sensor = modules.Get_Data_From_Azure_Table(modules.AZURE_TABLE_KEYS['mcpred'][0],modules.AZURE_TABLE_KEYS['mcpred'][1], farm+predictor+sensor_id)
    data_df = pd.DataFrame(data_sensor)
    data_df["LastSensorTime"] = pd.to_datetime(data_df["LastSensorTime"])
    first_ts_pred = data_df["LastSensorTime"][0].strftime('%Y-%m-%dT%H:%M:%S')
    data_df = data_df.set_index('LastSensorTime')
    data_df = data_df.loc[~data_df.index.duplicated(keep='last')]

    sensor_data_df = modules.get_sensor_box_data(first_ts_pred,sensor_id=sensor_id,table=farm,frequency="1")

    #sensor_data_df = modules.rename_sensor_df(sensor_data_df)
    y,yhat=list(),list()
    for index, _ in sensor_data_df.iterrows():
        try:
            temp_y = sensor_data_df[predictor][index+pd.DateOffset(hours=ts_lookahead)].astype(float)
            temp_yhat = float(data_df['Predicted'+predictor+ str(ts_lookahead) + 'Hour'][index])
            y.append(temp_y)
            yhat.append(temp_yhat)

        except KeyError:
            continue
            
            
    return y,yhat

def model_validation(sensor_id, location, n_pred_var, server_mode=False, station='DS'):
    
    model = load_model('model_humidity_ws_ds_forecast_cnnLSTM.h5')
    
    update_freq_hours = 24*30*10
    if station=='DS':
        current_time = datetime.utcnow()
        start_time = current_time - timedelta(hours=update_freq_hours)
        data_df = modules.get_combined_data_ws_gs(start_time.strftime("%Y-%m-%dT%H:%M:%S"), frequency="1",sensor_id=sensor_id,location=location,only_forecast=False, station='DS')
    else:
        end_time = "20190820"
        current_time = datetime.strptime(end_time,"%Y%m%d")
        start_time = current_time - timedelta(hours=update_freq_hours)
        data_df = modules.get_combined_data_ws_gs(start_time.strftime("%Y-%m-%dT%H:%M:%S"), frequency="1",sensor_id=sensor_id,location=location,only_forecast=False, station="NOAA CSV", end_time=end_time)
        
        
        
    scaler_y, train_X, train_y, test_X, test_y = modules.convert_df_wavelet_training_set(data_df,n_pred_var=n_pred_var,validation = True, per_split=0.5)
    print
    validation_data = [test_X,test_y]
    batch_size = 8
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
    yhat = scaler_y.inverse_transform(model.predict(test_X))
    
    return model, history, yhat, scaler_y.inverse_transform(test_y)

def model_stock_validation(sensor_id, location, n_pred_var, station='DS'):
    
    model = load_model('model_humidity_ws_ds_forecast_cnnLSTM.h5')
    
    update_freq_hours = 24*30*5
    
    if station=='DS':
        current_time = datetime.utcnow()
        start_time = current_time - timedelta(hours=update_freq_hours)
        data_df = modules.get_combined_data_ws_gs(start_time.strftime("%Y-%m-%dT%H:%M:%S"), frequency="1",sensor_id=sensor_id,location=location,only_forecast=False, station='DS')
    else:
        end_time = "20190820"
        current_time = datetime.strptime(end_time,"%Y%m%d")
        start_time = current_time - timedelta(hours=update_freq_hours)
        data_df = modules.get_combined_data_ws_gs(start_time.strftime("%Y-%m-%dT%H:%M:%S"), frequency="1",sensor_id=sensor_id,location=location,only_forecast=False, station="NOAA CSV", end_time=end_time)
    
    scaler_y, train_X, train_y, test_X, test_y = modules.convert_df_wavelet_training_set(data_df,n_pred_var=n_pred_var,validation = True, per_split=0.5)
    print
    
    yhat = scaler_y.inverse_transform(model.predict(test_X))
    
    return model, yhat, scaler_y.inverse_transform(test_y)