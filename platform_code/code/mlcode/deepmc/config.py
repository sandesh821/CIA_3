#Copyright (c) Microsoft. All rights reserved.
from  datetime import datetime
import os

# CONFIGURATION FOR Live Source Storage account 
src_account_name = "ayanadeepmcstoredev"
src_kvname = "solarlivedatablob"
src_container_name = "datasets"

# CONFIGURATION FOR Storage account reffered by DEEPMC Forecast models
model_account_name = "dmc12a3da3fcf8adls"
deepmc_kvname = "deepmcblob"
model_src_container = "datasets"
model_pred_container = "predictions"
kv_name = "ayanadeepmckeyvault"

# model_account_name = "dm1kpt12f12f623adls"
# deepmc_kvname = "deepmcblob"
# model_src_container = "datasets"
# model_pred_container = "predictions"
# kv_name = "ayanadeepmckeyvault"
kv_pass = "FSeCP/zUX1MjKVcLH2OeiLzSLVFZa/Gtw38ZwECBYtz4n/ILBMEMRCr+vTkfyq7nkBvNDozroDk1jqoU6iNBHA=="


#CONFIGURATION FOR MAIL NOTIFICATION 
mailapi_kvname = "mailapikey"
email_from = "hbobbala@microsoft.com"
email_to = "hbobbala@microsoft.com"

root_dir = 'C:\\DeepMC\\python'

LOGS_DIR = 'logs'

location = "Asia/Kolkata"

param =  {
'Block2' : {
    # Configuration for RADIATION FORECAST API CALL 
    #'ip' : "",
    'Blockno' : "Block2",
    #'Exp_Id' : 'e85c6678f7a345c38e4c88f9cecfb0f9', # 3.3 symmetric 'e6465c26d82543149b9f461e03812963'  ,# 2.2 periodic '17eadd56d79844478a945990c1f3c336',#bio 2.2 symm 'f134ab42f73342e193225ba17f84a68e', #bior3.5'cae59f19cb054825bd028a27a46b8417',#db3 'cafc74ab303041b4946271982762e849' ,# yhat6yhat11 '0b0e42aa408244eb8a60628d2e122e1b',#db5 'e85c6678f7a345c38e4c88f9cecfb0f9', #'311690ad478940f888441b01658034a5',#march model,#'50f273ed3e11488f930c0b2f962c2d49' ,#'e483837509404465892a937ebe543930',#'b63f64bf476b4f819baffe4624c182fe',#'b63f64bf476b4f819baffe4624c182fe',#sept 'ea29f1cc11ac41238ff5645d513d3c1d',#'f3e9f5028b6e46d0a889d98378963f55',#'a6a2fa510b6d435cbb2c1eecad0978e1',#'cc3b8f45da28464eadba1868eab0b526',#'a6a2fa510b6d435cbb2c1eecad0978e1' ,#,#'b2cf78fba6584e85b17d7def248e38a1', #'cc3b8f45da28464eadba1868eab0b526',#'e2fd2d202ae14302b1e8f0507cac7325', #'4fe5c2522b2d4b80ba376b2dab1165ee',#'944762f8348d49f398aaf6d75b6f8881',
    'farm_name' :   "Pav1",# "GuruTestFarm",
    'experiment_name' : 'ST_3hr', #"val",
    'equipment_id' : 'Block2_ST1', #"Block1",
    'model_name' :  'till_august',#"AyanaSTModel",
    'training_type' : "DeepMC",
    'target' : "Radiation",
    'epochs': "150",
    'lookback' :"24" , 
    'lookbackhrs' : 6,
    'lookahead' : "12",
    'frequency_str' : "15min",
    'lookback_str' :  '24',
    'lookahead_str' : '12',
    'duration' :'ST',
    'forecast_file_path' : 'ayana_test',#"Block2\\Predict",
    'container_predictions' :  "predictions",
    'container_datasets' : "datasets",
    'Features_list' : ['B2_MAIN_PLC..B2_OG_ACTIVE_POWER_MWH','B2_ICR_4..B2_ICR_4_GII_WM2', 'B2_MAIN_PLC.B2_CALCI.B2_WMS.WIND_DIRECTION',
        'B2_MAIN_PLC.B2_CALCI.B2_WMS.WIND_SPEED', 'B2_MAIN_PLC.B2_CALCI.B2_WMS.AIR_TEMPERATURE', 'B2_MAIN_PLC.B2_CALCI.B2_WMS.MODULE_TEMPERATURE',
        'B2_MAIN_PLC.B2_CALCI.B2_WMS.HUMIDITY'],
    'col_list' : ['timestamp', 'itemname','value'],
    'CONSQ_MISS_POINTS' : 100000 ,
    'threshold_diff':100000,
    'validation_filename':"C:/deepmc/python/AK_Block2_May_May/Block2_train/DeepMC/Validate_Block2_July/ForecastResults_Block2_July_Block2_Akanksha_May20_May21.csv",
    'rename_columns' : {'timestamp': 'DateTime', 
                                    'B2_ICR_4..B2_ICR_4_GII_WM2': 'TILT(Wpm2)', 
                                    'B2_MAIN_PLC..B2_OG_ACTIVE_POWER_MWH': 'ActualPower',
                                    'B2_MAIN_PLC.B2_CALCI.B2_WMS.WIND_DIRECTION': 'WDIR(deg)',
                                    'B2_MAIN_PLC.B2_CALCI.B2_WMS.WIND_SPEED': 'WSPD(Kmph)',
                                    'B2_MAIN_PLC.B2_CALCI.B2_WMS.AIR_TEMPERATURE': 'ATMP(degC)',
                                    'B2_MAIN_PLC.B2_CALCI.B2_WMS.MODULE_TEMPERATURE': 'MTMP(degC)',
                                    'B2_MAIN_PLC.B2_CALCI.B2_WMS.HUMIDITY': 'HUMD(per)'},
    'power_hyper_params' : {
        'task': 'train',
        'boosting_type': 'gbdt',
        'objective': 'regression',
        'metric': ['mse', 'mape'],
        'learning_rate': 0.005,
        'feature_fraction': 0.9,
        'bagging_fraction': 0.7,
        'bagging_freq': 10,
        'verbose': 0,
        "max_depth": 8,
        "num_leaves": 128,  
        "max_bin": 512,
        "num_iterations": 100000,
        "n_estimators": 1000
        }},

'Block1' : {
    # Configuration for RADIATION FORECAST API CALL 
    'ip' : "",
    'Blockno' : "Block1",
    'Exp_Id' : '',
    'farm_name' : "Pav1",
    'experiment_name' : "ST_3hr",
    'equipment_id' : "Block1_ST",
    'model_name' : "till_august",
    'training_type' : "DeepMC",
    'target' : "Radiation",
    'epochs': "2",
    'lookback' :"24" , # 24*15 -> 6 hour
    'lookbackhrs' : 6,
    'lookahead' : "12",
    'frequency_str' : "15min",
    'lookback_str' :  '24',
    'lookahead_str' : '12',
    'forecast_file_path' : "Block1\\Predict"
    } 

    }

token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsIng1dCI6Imwzc1EtNTBjQ0g0eEJWWkxIVEd3blNSNzY4MCIsImtpZCI6Imwzc1EtNTBjQ0g0eEJWWkxIVEd3blNSNzY4MCJ9.eyJhdWQiOiJhcGk6Ly8wMjljZjdiMC0wZGM1LTQxMTUtYTZlMi00MTE0YjNkNzhmYmYiLCJpc3MiOiJodHRwczovL3N0cy53aW5kb3dzLm5ldC9lMWMwOGFjMS00YzJlLTQ4NjktODMwZi05ZDcxNDZkODlhMTUvIiwiaWF0IjoxNjMxNDg5MzY5LCJuYmYiOjE2MzE0ODkzNjksImV4cCI6MTYzMTQ5MzI2OSwiYWNyIjoiMSIsImFpbyI6IkFYUUFpLzhUQUFBQXEyMUtPVkxnczQzUXpZRFpFRFFGOHg5U2QvNTRRU0FxSWp1RU5pWUxUSFlkNTB6MlZvYi9mV1Fzb3l0M3lDbTA4aTFXMHZYUVVFandFSkVpMVE0VDJyYzBFTVNWa1orczM3OWdLYjJVaTFURVIzSnRCVWE0M1FuSTRMalQ3SWsyYS9lWFp1bDNqNUU0Wll5eU5WZ1BEUT09IiwiYW1yIjpbInJzYSJdLCJhcHBpZCI6IjE3YmQxY2Q2LTNlY2ItNGY5YS1iNDc2LTI2MWIzZmEwNzdiNCIsImFwcGlkYWNyIjoiMSIsImVtYWlsIjoicHJrb21pcmVAbWljcm9zb2Z0LmNvbSIsImlkcCI6Imh0dHBzOi8vc3RzLndpbmRvd3MubmV0LzcyZjk4OGJmLTg2ZjEtNDFhZi05MWFiLTJkN2NkMDExZGI0Ny8iLCJpcGFkZHIiOiIxODMuODMuMTM5LjEwNiIsIm5hbWUiOiJQcmF0aW1hIFJlZGR5Iiwib2lkIjoiNTcxMGViMmMtN2Q0Mi00YzQ0LWE5ZjUtMDRjN2UxZjRkZDJjIiwicmgiOiIwLkFYQUF3WXJBNFM1TWFVaURENTF4UnRpYUZkWWN2UmZMUHBwUHRIWW1Hei1nZDdSd0FJcy4iLCJzY3AiOiJEZWVwTUMuQWNjZXNzIiwic3ViIjoieGE0MS16SHVGbklXLTNYWEg5cDN6RG1vMmF0cjducmZuR2k0WE43b21vZyIsInRpZCI6ImUxYzA4YWMxLTRjMmUtNDg2OS04MzBmLTlkNzE0NmQ4OWExNSIsInVuaXF1ZV9uYW1lIjoicHJrb21pcmVAbWljcm9zb2Z0LmNvbSIsInV0aSI6IjMxbHYtVk5nMEVHVDJJWHJjSFNKQUEiLCJ2ZXIiOiIxLjAifQ.Bd_1kmibx5k5THt2ujP1gzjxeqr-H0r4j_uy2k1kf_jvtAiSFGRBva-yKWTgzy33TRxoM3V-c8eGBv35wr8gYUR9nHV2je9bsb76Fy7I6J50yngB-NiSIBDFZ62IyZGaI093yPtaTe02qEZ5sZPwnDAIA9B7PEuTrLuLStVrjWDq42hPT_g2vamS9dcW_xpogHZN5dcJZQe8A0uCtFC6DMl2LyluttHseXF-Em-KTjjsqPthqEjzR-BRc1tdTnq06tJoTqMGq_yY-OwCHJ6YnYPiCFaRUm2cmraOjys23nGWrvq4HfubZlbAotosuClGDRX-ZVXCfLS1qsruSvySmQ"
