#Copyright (c) Microsoft. All rights reserved.
import requests
import pandas as pd
import numpy as np
from datetime import datetime  
from datetime import timedelta  
import pywt
import pickle
from time import sleep
from deepmc import models
from deepmc import modules

def convert_df_wavelet_input(data_df,n_pred_var = 'WindSpeed',wb=True, ts_lookback=24, ts_lookahead=24,wavelet='bior2.2',mode='periodic'):
    # Number of wavelet levels
    level = 5
    
    # Preprocess original signal
    _, _, _, test_y, _, _ = models.dl_preprocess_data(data_df.iloc[-ts_lookback- ts_lookahead:],ts_lookback=ts_lookback,ts_lookahead=ts_lookahead,pred_var_idx=[n_pred_var],validation=False)

    data_df = data_df.iloc[:-ts_lookahead]
    
    # Wavelets transform
    wp5 = pywt.wavedec(data=data_df[n_pred_var], wavelet=wavelet, mode=mode,level=level)
    rd = list()
    N = data_df.shape[0]

    # Preprocess transformed dataset
    for i in range(1,level+1):
        rd.append(pywt.waverec(wp5[:-i] + [None] * i, wavelet=wavelet, mode=mode)[:N])
    
    _, _, t_test_X, _, _, _ = models.dl_preprocess_data(data_df.iloc[-ts_lookback:],ts_lookback=ts_lookback,ts_lookahead=ts_lookahead,pred_var_idx=[n_pred_var],validation=False, training=False)

    test_X = list()
    test_X.append(t_test_X[[-1],:,:])
    wpt_df = data_df[[]].copy()

    for i in range(0,level):
        wpt_df[n_pred_var] = rd[i][:]
        _, _, t_test_X, _,_,_ = models.dl_preprocess_data(wpt_df.iloc[-ts_lookback:], 
                                                                 ts_lookback=ts_lookback,ts_lookahead=ts_lookahead,
                                                                   pred_var_idx=[n_pred_var],validation=False, training=False)
        
        test_X.append(t_test_X[[-1],:,:])
        
    return None, None, None, None, test_X, test_y[[-1],:,:]