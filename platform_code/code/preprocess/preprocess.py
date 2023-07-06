#Copyright (c) Microsoft. All rights reserved.

from os import environ as env
import azure
import pandas as pd
import numpy as np
import sys, os
import datetime
from MissingValuesHandler import *
from azureml.core import Run
import os
import argparse
import random
import yaml
import ast
import re
from azureml.core import Dataset,Datastore
from  FeatureUtils import *
from datetime import datetime , timedelta
import logging
from constants import *

class ingestion() :
    def __init__(self,connection_config,preprocess_config) :
        
        self.connection_config = connection_config
        self.preprocess_config = preprocess_config
        self.datetime_col_applicable =  connection_config['datetime_col_applicable']
        self.datetime_col_available = connection_config['datetime_col_available']
        
        self.source_datetime_col = connection_config['source_datetime_col']

        self.merge_data  = connection_config['merge_data']

        self.dataset_start_time = preprocess_config['dataset_start_time']
        self.futureCovariates = preprocess_config['futureCovariates']
        self.lookahead = preprocess_config['future_covariate_lookahead']
        self.forecast_times_str = preprocess_config['future_covariate_times_str']        
        self.reindex_cols = preprocess_config['manage_column'][0]['reindex_cols']
        self.datastore_name = connection_config['datastore_name']
        self.frequency = preprocess_config['frequency']
        self.frequency_duration = preprocess_config['frequency_duration']
        self.freq = str(self.frequency) + self.frequency_duration

        multiplicationFactorDict = {"H":1, "min" : (60), "S" : (60*60)}
        self.multiplicationFactor = multiplicationFactorDict.get(self.frequency_duration)
        self.pred_freq = (24*self.multiplicationFactor) /(self.lookahead*self.frequency)  # per day frequency (minutes per hour * hours per day) / granulairty

    def unit_conversion(self,data_df):
        try : 
            for i in self.conversion_cols:
                data_df[i] = data_df[i] * (self.conversion_cols[i][1])
                logging.info("convesion from {} is completed".format(self.conversion_cols[i][0]))
            return data_df
        except Exception as UnitConversionError:
            logging.error('Error while unit conversion')
            raise UnitConversionError
    
    def resample(self,data_df):
        try:
            data_df = data_df.groupby(pd.Grouper(key='DateTime', freq=self.freq)).mean()
            data_df.reset_index(inplace=True)
            return data_df
        except Exception as ResampleError: 
            logging.error('Error while Resampling the data')
            raise ResampleError
            
    def valid_dateformat(self,dat):
        match_iso8601 = re.compile(regex_pattern).match
        try:            
            if match_iso8601(dat) is not None:
                return True
        except ValueError:
            logging.error('Invalid Date Format in the source')
        return False
    
    def read_blob(self,datastore,dataset_name) :
        try :
            dataset = Dataset.Tabular.from_delimited_files(path = [(datastore, dataset_name)])
            return dataset
        except Exception as SourceFileNotFound :
            logging.error('Source file not found')
            raise SourceFileNotFound
        
    def merge_files(self,datastore):
        try:
            if self.merge_data is not None :
                dataset = self.read_blob(datastore,self.merge_data)
                merge_df = dataset.to_pandas_dataframe()
                merge_df['DateTime'] = merge_df[self.source_datetime_col].astype('str')
                merge_df['DateTime'].apply(self.valid_dateformat)
                merge_df['DateTime'] = pd.to_datetime(merge_df['DateTime'])
        except Exception as SourceException : 
            logging.error('Error Occcured while loading entity data')
            raise SourceException
        return merge_df        

    def forecast_data_prep(self,df):
        col_lst = df.columns
        datetime_format_str = "%Y-%m-%d %H:%M:%S"
        if (self.datetime_col_applicable in col_lst)  & (self.datetime_col_available in col_lst ) :
            curr_date_str = self.dataset_start_time  # start date from config
            forecast_times_str = self.forecast_times_str # Intra forecast timings from config
            forecast_datetimes = []
            cleaned_final_df = pd.DataFrame(columns = df.columns)
            start_date = df[self.datetime_col_applicable].min()
            end_date = df[self.datetime_col_applicable].max()
            threshold_date = df[self.datetime_col_available].max()
            print(start_date,end_date)
            no_of_days = end_date-start_date
            no_of_days= no_of_days.days

            logging.info("========= Generate forecast datetimes =========")
            
            forecast_datetime = datetime.strptime("{} {}".format(curr_date_str,forecast_times_str[0]), datetime_format_str)
            for i in range(int(no_of_days * self.pred_freq)):
                forecast_datetimes.append(forecast_datetime  + timedelta(seconds = i * self.lookahead *  self.frequency * (3600/self.multiplicationFactor)))
            
            for i in range(len(forecast_datetimes)):
                temp_df = pd.DataFrame()
                predtime =  forecast_datetimes[i]
                start_date = df[df[self.datetime_col_applicable] <= predtime][self.datetime_col_available].max()
                if start_date == threshold_date :
                    break

                if len(df[ (df[self.datetime_col_available] == start_date) & (df[self.datetime_col_applicable] >= predtime)]) < self.lookahead :
                    logging.error('Forecast doesnt have enough forecast values')
                    raise Exception('Forecast doesnt have enough forecast values')
                else : 
                    temp_df = df[(df[self.datetime_col_available] == start_date) & (df[self.datetime_col_applicable] >= predtime)][: self.lookahead]
                cleaned_final_df = pd.concat([cleaned_final_df,temp_df], axis = 0 ) 
                
            cleaned_final_df.rename(columns = {self.datetime_col_applicable : 'DateTime'} , inplace  =True)
            cleaned_final_df['DateTime'] = pd.to_datetime(cleaned_final_df['DateTime'])
            return cleaned_final_df
        else : 
            logging.error('Available time or Applicable Time features are not available')
            raise Exception('Available time or Applicable Time features are not available')

if __name__ == '__main__' :

    parser = argparse.ArgumentParser()
    parser.add_argument('--output-data', type=str,dest = 'output', default = 'output' ,help='Directory to output the processed  data')
    parser.add_argument('--preprocess-config', type=str,dest = 'preprocess_config', default = 'preprocess_config' ,help='preprocess_config')
    parser.add_argument('--connection-config', type=str,dest = 'connection_config', default = 'connection_config' ,help='connection_config')
    args = parser.parse_args()

    try :
        preprocess_config = ast.literal_eval(args.preprocess_config)
        connection_config = ast.literal_eval(args.connection_config) 
    except Exception as ConfigurationError :
        logging.error('configuration error in config.yaml file')
        raise ConfigurationError

    dataingestion = ingestion(connection_config,preprocess_config)

    run = Run.get_context()
    exp = run.experiment
    ws = run.experiment.workspace
    datastore = Datastore.get(ws, datastore_name= dataingestion.datastore_name)

    # ***************************************
    # Merge the past and future covariates 
    # ***************************************
    logging.info('=====Start: Merging data=====')
    merge_df = dataingestion.merge_files(datastore)
    print(merge_df.columns)
    print(merge_df)
    logging.info('=====End: Merging data=====')

    # ***************************************
    # pass dataframe to impute missing values module and return processed data_df
    # ***************************************
    try:   
        logging.info('=====Start: Missing Value updates=====')
        misvalhandler = MissingValuesHandler(merge_df,connection_config,preprocess_config)
        data_df = misvalhandler.missing_main()
        logging.info('=====End: Missing Value updates=====')
    except Exception as MissingValueHandlerError :
        logging.error('Error occured while handling missing values')
        raise MissingValueHandlerError
   
    # ***************************************
    # create two datasets, with and without shift index
    # ***************************************

    data_df_cols = data_df.columns
    no_shift_data_df =data_df.copy()
    try:
        data_df[dataingestion.futureCovariates] = data_df[dataingestion.futureCovariates].shift(-1 * dataingestion.lookahead)
    except Exception as ShiftIndexError:
        logging.error('Error occured while shifting the data for DeepMC data')
        raise ShiftIndexError

    os.makedirs(args.output+'/data/',exist_ok = True)
    os.makedirs(args.output+'/deepmc_data/',exist_ok = True)
    no_shift_data_df.to_csv(os.path.join(args.output+'/data/','data.csv'))
    data_df.to_csv(os.path.join(args.output+'/deepmc_data/','deepmc_data.csv'))

    logging.info('preprocessing completed and files splitted in default datastore')