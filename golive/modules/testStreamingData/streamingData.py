#Copyright (c) Microsoft. All rights reserved.
import pandas as pd
import random
from datetime import datetime, timedelta
import os
import sys

# sys.path.insert(0,currentDir)

def generate_dataframe(num_rows=100, start_timestamp=None):
    print(start_timestamp)
    # Calculate a list of num_rows timestamps, starting with the starting timestamp and increasing by 60 minutes for each successive row
    timestamp_list_prev = [datetime.strftime(start_timestamp - timedelta(minutes=5*(num_rows-i)), "%Y-%m-%d %H:%M:%S") for i in range(num_rows)]
    # timestamp_list = [datetime.strftime(start_timestamp + timedelta(minutes=5*i), "%Y-%m-%d %H:%M:%S") for i in range(num_rows)]
    timestamp_list = timestamp_list_prev #+ timestamp_list

    # Create a list of num_rows random windspeed values between 1 and 25
    field_list_prev = [random.randint(1, 1000) for i in range(num_rows)]
    # Create a list of num_rows random windspeed values between 1 and 25
    # field_list = [random.randint(1, 1000) for i in range(num_rows)]
    field_list = field_list_prev #+ field_list

    # Create a list of num_rows random windspeed values between 1 and 25
    field2_list_prev = [random.randint(-10, 40) for i in range(num_rows)]
    # Create a list of num_rows random windspeed values between 1 and 25
    # field2_list = [random.randint(-10, 40) for i in range(num_rows)]
    field2_list = field2_list_prev #+ field2_list

    # Create a pandas DataFrame with "timestamp" and "windspeed" columns
    df = pd.DataFrame({"DateTime": timestamp_list, "iot_site_GHI": field_list, "iot_site_TmpC": field2_list})

    return df

def generate_entity(num_rows=100, start_timestamp=None):

    # Calculate a list of num_rows timestamps, starting with the starting timestamp and increasing by 30 minutes for each successive row
    timestamp_list_prev = [datetime.strftime(start_timestamp - timedelta(minutes=5*(num_rows-i)), "%Y-%m-%d %H:%M:%S") for i in range(num_rows)]
    # timestamp_list = [datetime.strftime(start_timestamp + timedelta(minutes=5*i), "%Y-%m-%d %H:%M:%S") for i in range(num_rows)]
    timestamp_list = timestamp_list_prev #+ timestamp_list

    # Create a list of num_rows random windspeed values between 1 and 25
    power_list_prev = [random.randint(0, 10000) for i in range(num_rows)]
    # Create a list of num_rows random windspeed values between 1 and 25
    # power_list = [random.randint(0, 10000) for i in range(num_rows)]
    power_list = power_list_prev #+ power_list

    # Create a pandas DataFrame with "timestamp" and "windspeed" columns
    df = pd.DataFrame({"DateTime": timestamp_list, "power_Power": power_list})

    return df

def generateData():
    df = generate_dataframe(3, start_timestamp=datetime.now())
    entity_df = generate_entity(3, start_timestamp=datetime.now())
    return df, entity_df