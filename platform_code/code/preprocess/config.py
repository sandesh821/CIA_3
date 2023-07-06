#Copyright (c) Microsoft. All rights reserved.
import os
from os import environ as env

#Environment Config
container_name = "blobdata"
secret_name = "forecastblobkey"
account_name = 'forecastdatapoc'

#Data Config
date_format = '%d %m %Y %H:%M'
tgt_col = 'power'
src_date_column = 'Date/Time'
src_filename = 'turkey_1hr_granularity.csv'
upload_filename = "upload_samplefile.csv"
src_filename1 = 'turkey_10min_granulairty.csv'
src_path = os.path.join(os.getcwd(),'data')
splitfiles_path = 'splitfiles'
gran = 60

#Missing values config
interpolate_cols = { 'WindDirection': ['linear','both'] }
stats_cols = {'power':'mean' , 'windspeed' : 'mean'}
MICE_cols = []
fill_cols = ['theor_power']

#Conversion Config
conversion_cols = { 'power': ['KW to MW',1/1000] }

frequency = '60min'

column_mapping = {'windspeed' : 'WindSpeed',
                'WindDirection' : 'WindDirection',
                'theor_power' : 'TheoriticalPower',
                'wind_bins' : 'WindBins',
                'power' : 'Power'}


output_path = os.path.join(os.getcwd(),'wind','output')
training_features = [ 'windspeed', 'theor_power', 'power']
features = ['DateTime','windspeed', 'theor_power', 'power']
# rename_columns = {'kW': 'power', 
#                             'TmpF': 'temperature', 
#                             'CloudOpacity': 'cloudopacity',
#                             'RelativeHumidity': 'humidity',
#                             'SurfacePressure': 'surfacepressure'}
seasons = {
11: "Autumn", 12: "Winter", 1: "Winter", 2: "Winter",
3:"Spring", 4:"Spring", 5:"Spring", 6:"Summer",
7:"Summer", 8:"Summer", 9:"Autumn", 10:"Autumn"
}
dat_col = 'DateTime'
scatter_cols = ['windspeed', 'theor_power']
windspeed_col = 'windspeed'

x_name = "wind speed"
y_name = "Power [KW]"
x_col = "windspeed"
y_col = "power"
granulairty = 60
