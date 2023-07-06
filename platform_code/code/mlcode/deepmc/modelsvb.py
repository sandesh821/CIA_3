#Copyright (c) Microsoft. All rights reserved.
import math
import tensorflow 
from tensorflow import keras
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from tensorflow.keras.layers import Flatten
from tensorflow.keras.layers import LSTM
from tensorflow.keras.layers import RepeatVector
from tensorflow.keras.layers import TimeDistributed
from tensorflow.keras.layers import ConvLSTM2D
from tensorflow.keras.activations import relu
from tensorflow.keras.layers import Conv1D, Input, concatenate, Dropout, BatchNormalization, Reshape
from statsmodels.tsa.arima_model import ARIMA
from tensorflow.keras.models import load_model
from tensorflow.keras.models import Model

import datetime, time
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt

def dl_preprocess_data(df, ts_lookback, ts_lookahead, pred_var_idx,validation=True,per_split=0.80, training=True):
    n_in = ts_lookback
        
    scaled_df = df
    data = scaled_df.values.astype(float)
    
    if training is True:
        n_out = ts_lookahead
        label_df = df.copy()
        for column in label_df:
            if column not in pred_var_idx:
                label_df.drop(columns=column,inplace=True)


        label_data = label_df.values

        #label_data = label_df.values
        X, y = list(), list()
        in_start = 0
        # step over the entire history one time step at a time
        # reshape input to be 3D [samples, timesteps, features]
        for _ in range(len(data)):
            # define the end of the input sequence
            in_end = in_start + n_in
            out_end = in_end + n_out
            # ensure we have enough data for this instance
            if out_end <= len(data):
                X.append(data[in_start:in_end, :])
                y.append(label_data[in_end:out_end, :])
            # move along one time step
            in_start += 1

        X = np.array(X)
        y = np.array(y)

        if validation is True:
            n_train_split = math.ceil(len(data)*per_split)
            train_X, train_y = X[:n_train_split, :,:], y[:n_train_split,:,:]
            test_X, test_y = X[n_train_split:, :], y[n_train_split:,:]

            return None, None, train_X, train_y, test_X, test_y
        else:
            return None, None, X, y,None,None
    else:
        X = list()
        in_start = 0
        # step over the entire history one time step at a time
        # reshape input to be 3D [samples, timesteps, features]
        for _ in range(len(data)-n_in+1):
            # define the end of the input sequence
            in_end = in_start + n_in
            # ensure we have enough data for this instance
            if in_end <= len(data):
                X.append(data[in_start:in_end, :])
            # move along one time step
            in_start += 1

        X = np.array(X)
        return None, None, X, None, None, None
    
def dl_pred_model(train_X, train_y, validation_data=None, server_mode=False):
    # design network
    n_timesteps, n_features, n_outputs = train_X.shape[1], train_X.shape[2], train_y.shape[1]
    model = Sequential()
    model.add(LSTM(100, input_shape=(n_timesteps, n_features),activation='relu',recurrent_dropout=0.2,dropout=0.2))
    
    model.add(RepeatVector(n_outputs))
    model.add(LSTM(100, activation='relu', return_sequences=True))
    leaky_relu = lambda x:  relu(x, alpha=0.0, max_value=None, threshold=0.0)
    model.add(TimeDistributed(Dense(150, activation=leaky_relu)))
    model.add(Dropout(0.2))
    model.add(TimeDistributed(Dense(1)))
    model.compile(loss='mse', optimizer='adam')
    # fit network
    history = model.fit(train_X, train_y, epochs=5, batch_size=4, validation_data=validation_data,verbose=1)
    # plot history
    if server_mode is False:
        plt.plot(history.history['loss'], label='train')
        if validation_data is not None:
            plt.plot(history.history['val_loss'], label='test')
        #plt.plot(history.history['val_acc'], label='Accuracy')

        plt.legend()
        plt.show()
    return model

def func_rmse(dataset1, dataset2, ignore=None):
    if type(dataset1).__module__ != np.__name__:
        d1 = np.asarray(dataset1).flatten()
    else:
        d1 = dataset1.flatten()

    if type(dataset2).__module__ != np.__name__:
        d2 = np.asarray(dataset2).flatten()
    else:
        d2 = dataset2.flatten()

    # Make sure that the provided data sets are the same size
    if d1.size != d2.size:
        raise ValueError('Provided datasets must have the same size/shape')

    # Check if the provided data sets are identical, and if so, return 0
    # for the root-mean-squared error
    if np.array_equal(d1, d2):
        return 0

    # If specified, remove the values to ignore from the analysis and compute
    # the element-wise difference between the data sets
    if ignore is not None:
        index = numpy.intersect1d(np.where(d1 != ignore)[0], 
                                np.where(d2 != ignore)[0])
        error = d1[index].astype(np.float64) - d2[index].astype(np.float64)
    else:
        error = d1.astype(np.float64) - d2.astype(np.float64)

    # Compute the mean-squared error
    meanSquaredError = np.sum(error**2) / error.size

    # Return the root of the mean-square error
    return np.sqrt(meanSquaredError)

def func_mape(y_true, y_pred):
    mape = 0
    count = 0
    for i in range(len(y_true)):
        if(y_true[i] > 0.01):
            mape = mape + np.abs((y_true[i] - y_pred[i])/ y_true[i])
            count += 1
    mape = mape / count * 100
          
    return mape

def func_nmape(y_true, y_pred):
    num = 0
    den = 0
    for i in range(len(y_true)):
        if(y_true[i] > 0.001):
            num = num + np.abs((y_true[i] - y_pred[i]))
            den = den + y_true[i]
    mape = num / den * 100
          
    return mape

def func_mase(training_series, testing_series, prediction_series):
    """
    Computes the MEAN-ABSOLUTE SCALED ERROR forcast error for univariate time series prediction.
    
    See "Another look at measures of forecast accuracy", Rob J Hyndman
    
    parameters:
        training_series: the series used to train the model, 1d numpy array
        testing_series: the test series to predict, 1d numpy array or float
        prediction_series: the prediction of testing_series, 1d numpy array (same size as testing_series) or float
        absolute: "squares" to use sum of squares and root the result, "absolute" to use absolute values.
    
    """
    n = training_series.shape[0]
    d = np.abs(  np.diff( training_series) ).sum()/(n-1)
    
    errors = np.abs(testing_series - prediction_series )
    return errors.mean()/d

def func_mae(y_true, y_pred):
    return np.mean(np.abs((y_true - y_pred)))

def retrain_n_predict(validation=False,server_mode=True):
    ts_lookback=12
    ts_lookahead=12
    
    scaler, scaler_y, train_X, train_y = dl_preprocess_data(data_df,validation=validation,ts_lookback=ts_lookback, ts_lookahead=ts_lookahead)
    
    model = pred_model(train_X, train_y, server_mode=server_mode)
    
    X_df = data_df[-ts_lookback:]
    X = scaler.fit_transform(X_df)
    X = X.reshape((1,X.shape[0],X.shape[1]))
    
    yhat = scaler_y.inverse_transform(model.predict(X))[0,:,0].astype(str).tolist()
    
    current_time = str(X_df[-1:].index[0])
    
    entity = Entity()
    entity.TimeStamp = EntityProperty(EdmType.DATETIME, datetime.datetime.utcnow())
    entity.LastSensorTime = EntityProperty(EdmType.STRING, current_time)
    
    ts = 0
    
    for val in yhat:
        ts = ts + 1
        entity["PredictedTemperature" + str(ts) + "Hour"]=val
    
    
    return entity

def tseries_to_output(tseries, ts=24):
    output = list()
    for idx in range(0,len(tseries)-ts):
        output.append(tseries[idx:idx+ts].T[0])
    return output

def ticks(time_stamp: datetime.datetime):
    return int((time_stamp - datetime.datetime(1, 1, 1)).total_seconds() * 10000000)

def arima_pred_model(df, ts_lookahead=24, pred_var_idx=["_Ambient Temperature"], server_mode=True, per_split=0.99):
    
    df = df[pred_var_idx]
    X = df.values
    if server_mode is False:
        size = int(len(X) * per_split)
        train, test = X[0:size], X[size:len(X)]
        history = [x for x in train]
        predictions = list()
        for t in range(len(test)):
            model = ARIMA(history, order=(5,1,0))
            model_fit = model.fit(disp=0)
            output = model_fit.forecast(steps=ts_lookahead)
            yhat = output[0]
            predictions.append(yhat)
            obs = test[t]
            history.append(obs)
            print(t)
        test = tseries_to_output(test, ts=ts_lookahead)
        return pd.DataFrame(predictions), train, test
            #print('predicted=%f, expected=%f' % (yhat, obs))
    else:
        size = int(len(X)-ts_lookahead)
        train, test = X[0:size], X[size:len(X)]
        history = [x for x in train]
        predictions = list()
        for t in range(len(test)):
            model = ARIMA(history, order=(5,1,0))
            model_fit = model.fit(disp=0)
            output = model_fit.forecast(steps=ts_lookahead)
            yhat = output[0]
            predictions.append(yhat)
            obs = test[t]
            history.append(obs)
        test = tseries_to_output(test, ts=ts_lookahead)
        return pd.DataFrame(predictions)[ts_lookahead-1]
    
def cnn_layers(train_X, kernel_size=4):
    n_timesteps, n_features = train_X.shape[1], train_X.shape[2]
    in1 = Input(shape=(n_timesteps, n_features,))
    conv1 = Conv1D(2,kernel_size,strides=1,activation='relu', kernel_initializer='he_normal')(in1)
    conv1 = BatchNormalization()(conv1)
    conv2 = Conv1D(4,kernel_size,strides=1,activation='relu', kernel_initializer='he_normal')(conv1)
    conv2 = BatchNormalization()(conv2)
    conv3 = Conv1D(8,kernel_size,strides=1,activation='relu', kernel_initializer='he_normal')(conv2)

    flat1 = Flatten()(conv3)

    
    return in1, flat1

def cnnlstm_layers(train_X,kernel_size=4):
    # design network
    n_timesteps, n_features = train_X.shape[1], train_X.shape[2]
    in1 = Input(shape=(n_timesteps, n_features,))
    conv1 = Conv1D(4,kernel_size,activation='relu', kernel_initializer='he_normal')(in1)
    conv1 = BatchNormalization()(conv1)
    conv2 = Conv1D(8,kernel_size,activation='relu', kernel_initializer='he_normal')(conv1)
    conv2 = BatchNormalization()(conv2)
    lstm1 = LSTM(4, activation='relu', return_sequences=False,recurrent_dropout=0.4,dropout=0.4)(conv2)
    
    return in1,lstm1

def lstm_layers(train_X):
    # design network
    n_timesteps, n_features = train_X.shape[1], train_X.shape[2]
    in1 = Input(shape=(n_timesteps, n_features,))
    lstm1 = LSTM(4, activation='relu', return_sequences=False)(in1)
    return in1,lstm1
    
def deepmc_pred_model(train_X, train_y, validation_data=None, server_mode=False, batch_size = 16):
    
    n_outputs = train_y.shape[1]
    
    inputs = list()
    flat = list()
    
    k=0
    kernel_size = [2,2,2,2,2]
    for i in range(0,1):
        t_in, t_flat = cnn_layers(train_X[k],kernel_size[k])
        inputs.append(t_in)
        flat.append(t_flat)
        k = k +1
    
    for i in range(k,len(train_X)):
        t_in, t_flat = cnnlstm_layers(train_X[k])
        inputs.append(t_in)
        flat.append(t_flat)
        k=k+1
        
        
    ##Attention Mechanism    
    merge = concatenate(flat)

    ##Decoder
    repeat1 = RepeatVector(n_outputs)(merge)
    lstm2 = LSTM(4, activation='relu', return_sequences=True)(repeat1)
    dense1 = TimeDistributed(Dense(16, activation='relu'))(lstm2)
    output = TimeDistributed(Dense(1))(dense1)
    
    ##Model Creation
    model = Model(inputs=inputs, outputs=output)
    model.compile(loss='mse', optimizer='adam')
    return model

def deepmc_fit_model(model, train_X, train_y, validation_data=None, server_mode=False,  params={}):
    batch_size = params.get("batch_size")
    # fit network
    epochs = params.get("epochs")
    history = model.fit(train_X, train_y, epochs=epochs, batch_size=batch_size, validation_data=validation_data,verbose=1)
    
    # Model evaluation
    score = model.evaluate(validation_data[0], validation_data[1], verbose=0)
    print('Test loss:', score[0])
    print('Test metric:', score[1])

    # plot history
    if server_mode is False:
        plt.plot(history.history['loss'], label='train')
        if validation_data is not None:
            plt.plot(history.history['val_loss'], label='test')

        plt.legend()
        plt.show()
    return model, score[1]

def deepmc_wextmodel_pred_model(train_X, train_y, ext_model_input, validation_data=None, server_mode=False):
    n_outputs = train_y.shape[1]

    inputs = list()
    flat = list()

    k=0
    kernel_size = [2,2,2,2,2]
    for i in range(0,len(train_X)-1):
        t_in, t_flat = models.cnn_layers(train_X[k],kernel_size[k])
        inputs.append(t_in)
        flat.append(t_flat)
        k = k +1

    for i in range(k,len(train_X)):
        t_in, t_flat = models.cnnlstm_layers(train_X[k])
        inputs.append(t_in)
        flat.append(t_flat)
        k=k+1
    ##Scale Attention Mechanism
    merge = concatenate(flat)

    repeat1 = RepeatVector(n_outputs)(merge)
    
    ##Decoder
    lstm2 = LSTM(2, activation='relu', return_sequences=True)(repeat1)
    dense1 = TimeDistributed(Dense(16, activation='relu'))(lstm2)
    deepmc_output = TimeDistributed(Dense(1))(dense1)
    
    ##Model Attention Mechanism
    n_timesteps = ext_model_input.shape[1]
    n_features = ext_model_input.shape[2]
    in_ext_model = Input(shape=(n_timesteps, n_features,))
    inputs.append(in_ext_model)
    merge_outputs = concatenate([deepmc_output,in_ext_model], axis=2)
    merge_outputs2 = BatchNormalization()(merge_outputs)
    output = TimeDistributed(Dense(1))(merge_outputs2)

    model = Model(inputs=inputs, outputs=output)
    model.compile(loss='mse', optimizer='adam')
    # fit network
    train_data = train_X.copy()
    train_data.append(ext_model_input)
    history = model.fit(train, train_y, epochs=30, batch_size=batch_size, validation_data=validation_data,verbose=1)
    # plot history
    if server_mode is False:
        plt.plot(history.history['loss'], label='train')
        if validation_data is not None:
            plt.plot(history.history['val_loss'], label='test')

        plt.legend()
        plt.show()
    return model

def deepmc_multiple_wextmodel_pred_model(train_X, train_y, ext_model_inputs, validation_data=None, server_mode=False):
    n_outputs = train_y.shape[1]

    inputs = list()
    flat = list()

    k=0
    kernel_size = [2,2,2,2,2]
    for i in range(0,len(train_X)-1):
        t_in, t_flat = models.cnn_layers(train_X[k],kernel_size[k])
        inputs.append(t_in)
        flat.append(t_flat)
        k = k +1

    for i in range(k,len(train_X)):
        t_in, t_flat = models.cnnlstm_layers(train_X[k])
        inputs.append(t_in)
        flat.append(t_flat)
        k=k+1
    ##Scale Attention Mechanism
    merge = concatenate(flat)
    repeat1 = RepeatVector(n_outputs)(merge)
    
    ##Decoder
    lstm2 = LSTM(2, activation='relu', return_sequences=True)(repeat1)
    dense1 = TimeDistributed(Dense(16, activation='relu'))(lstm2)
    #dropout1 = Dropout(0.2)(dense1)
    deepmc_output = TimeDistributed(Dense(1))(dense1)
    
    
    in_ext_model = []
    
    for ext_model_input in ext_model_inputs:
        ##Model Attention Mechanism
        n_timesteps = ext_model_input.shape[1]
        n_features = ext_model_input.shape[2]
        temp_ext_model = Input(shape=(n_timesteps, n_features,))
        
        inputs.append(temp_ext_model)
        in_ext_model.append(temp_ext_model)
        
        
    merge_outputs = concatenate(deepmc_output.append(in_ext_model), axis=2)
    merge_outputs2 = BatchNormalization()(merge_outputs)
    output = TimeDistributed(Dense(1))(merge_outputs2)

    model = Model(inputs=inputs, outputs=output)
    model.compile(loss='mse', optimizer='adam')
    # fit network
    train_data = train_X.copy()
    train_data.append(ext_model_input)
    history = model.fit(train_data, train_y, epochs=30, batch_size=batch_size, validation_data=validation_data,verbose=1)
    # plot history
    if server_mode is False:
        plt.plot(history.history['loss'], label='train')
        if validation_data is not None:
            plt.plot(history.history['val_loss'], label='test')
        #plt.plot(history.history['val_acc'], label='Accuracy')

        plt.legend()
        plt.show()
    return model

def deepmc_wextscales_pred_model(train_X, train_y, ext_model_scales, ext_model_input, validation_data=None, server_mode=False):
    batch_size = 16
    
    n_outputs = train_y.shape[1]
    
    inputs = list()
    flat = list()
    
    k=0
    kernel_size = [2,2,2,2,2]
    for i in range(0,len(train_X)-1):
        t_in, t_flat = cnn_layers(train_X[k],kernel_size[k])
        inputs.append(t_in)
        flat.append(t_flat)
        k = k +1
    
    for i in range(k,len(train_X)):
        t_in, t_flat = cnnlstm_layers(train_X[k])
        inputs.append(t_in)
        flat.append(t_flat)
        k=k+1
        
    inputs.append(ext_model_input)
    flat.append(ext_model_scales)
    
    ##Attention Mechanism    
    merge = concatenate(flat)

    ##Decoder
    repeat1 = RepeatVector(n_outputs)(merge)
    lstm2 = LSTM(2, activation='relu', return_sequences=True)(repeat1)
    dense1 = TimeDistributed(Dense(16, activation='relu'))(lstm2)
    output = TimeDistributed(Dense(1))(dense1)
    
    ##Model Creation
    model = Model(inputs=inputs, outputs=output)
    model.compile(loss='mse', optimizer='adam')
    # fit network
    history = model.fit(train_X, train_y, epochs=30, batch_size=batch_size, validation_data=validation_data,verbose=1)
    # plot history
    if server_mode is False:
        plt.plot(history.history['loss'], label='train')
        if validation_data is not None:
            plt.plot(history.history['val_loss'], label='test')
        plt.legend()
        plt.show()
    return model

def cnn_vanila_pred_model(train_X, train_y, validation_data=None, server_mode=False):
    batch_size = 16
    
    n_outputs = train_y.shape[1]
    train_X = train_X[0]
    train_y = train_y[:,:,0]
    if validation_data is not None:
        validation_data=[validation_data[0][0], validation_data[1][:,:,0]]
    inputs, flat = cnn_layers(train_X)
    
    hidden1 = Dense(20, activation='relu')(flat)
    hidden2 = Dense(10, activation='relu')(hidden1)
    output = Dense(1)(hidden2)
    
    model = Model(inputs=inputs, outputs=output)
    model.compile(loss='mse', optimizer='adam')
    # fit network
    history = model.fit(train_X, train_y, epochs=30, batch_size=batch_size, validation_data=validation_data,verbose=1)
    # plot history
    if server_mode is False:
        plt.plot(history.history['loss'], label='train')
        if validation_data is not None:
            plt.plot(history.history['val_loss'], label='test')
        #plt.plot(history.history['val_acc'], label='Accuracy')

        plt.legend()
        plt.show()
    return model

def lstm_vanila_pred_model(train_X, train_y, validation_data=None, server_mode=False):
    batch_size = 16
    
    n_outputs = train_y.shape[1]
    train_X = train_X[0]
    train_y = train_y[:,:,0]
    if validation_data is not None:
        validation_data=[validation_data[0][0], validation_data[1][:,:,0]]
    
    inputs, flat = lstm_layers(train_X)
    
    #hidden1 = Dense(10, activation='relu')(merge)
    #output = Dense(1)(hidden1)
    output = Dense(24)(flat)
    
    model = Model(inputs=inputs, outputs=output)
    ##plot_model(model, to_file='wdpcnn_arch6.png',show_shapes=True)
    model.compile(loss='mse', optimizer='adam')
    # fit network
    history = model.fit(train_X, train_y, epochs=15, batch_size=batch_size, validation_data=validation_data,verbose=1)
    # plot history
    if server_mode is False:
        plt.plot(history.history['loss'], label='train')
        if validation_data is not None:
            plt.plot(history.history['val_loss'], label='test')

        plt.legend()
        plt.show()
    return model

def cnnlstm_pred_model(train_X, train_y, validation_data=None, server_mode=False):
    batch_size = 16
    
    n_outputs = train_y.shape[1]
    train_X = train_X[0]
    train_y = train_y[:,:,0]
    if validation_data is not None:
        validation_data=[validation_data[0][0], validation_data[1][:,:,0]]
    inputs, flat = cnnlstm_layers(train_X)
    
    hidden1 = Dense(10, activation='relu')(flat)
    output = Dense(1)(hidden1)
    model = Model(inputs=inputs, outputs=output)
    model.compile(loss='mse', optimizer='adam')
    # fit network
    history = model.fit(train_X, train_y, epochs=10, batch_size=batch_size, validation_data=validation_data,verbose=1)
    # plot history
    if server_mode is False:
        plt.plot(history.history['loss'], label='train')
        if validation_data is not None:
            plt.plot(history.history['val_loss'], label='test')
        #plt.plot(history.history['val_acc'], label='Accuracy')

        plt.legend()
        plt.show()
    return model
  
