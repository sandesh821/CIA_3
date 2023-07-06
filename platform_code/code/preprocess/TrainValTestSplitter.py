#Copyright (c) Microsoft. All rights reserved.
from os import environ as env
import pandas as pd
import numpy as np
import sys, os
#from config import *
import datetime
import os

# class BlobStorageManager
# download from blob
# upload to blob

class TrainValTestSplitter() :

    def __init__(self,preprocess_config) :
        self.gran = preprocess_config['frequency']
        self.day_points = (60*24)/self.gran
        self.splitByDate = preprocess_config['splitByDate']
        self.trainsplitDate = preprocess_config['trainsplitDate']
        self.valsplitDate = preprocess_config['valsplitDate']
        self.testsplitDate = preprocess_config['testsplitDate']
        self.trainsplit = float(preprocess_config['trainsplit'])
        self.valsplit = float(preprocess_config['valsplit'])
        self.testsplit = float(preprocess_config['testsplit'])

    def get_split_point(self,data_df):
        
        if self.splitByDate == True:
            training_cutoff = len(data_df[data_df['DateTime'] < self.trainsplitDate ])
            val_cutoff = len(data_df[data_df['DateTime'] < self.valsplitDate ])
            test_cutoff = len(data_df[data_df['DateTime'] < self.testsplitDate ])
        else:
            print(len(data_df))
            print(self.trainsplit)
            training_cutoff = int(len(data_df)*self.trainsplit)
            val_cutoff = int(len(data_df)*self.valsplit) + training_cutoff
            test_cutoff = int(len(data_df)*self.testsplit) + val_cutoff
        
        return training_cutoff,val_cutoff,test_cutoff


    def train_val_test_split(self,data_df):

        max_date = data_df['DateTime'].max()
        maxdaycount = len(data_df[data_df['DateTime'].dt.date == max_date.date()])
        #maxdaybeforecount = len(data_df[data_df['DateTime'].dt.date == max_date.date()-timedelta(days = 1)])
        if maxdaycount != self.day_points:
            data_df = data_df[data_df['DateTime'].dt.date < max_date.date()]
            print(data_df['DateTime'].max())
        
        min_date = data_df['DateTime'].min()
        mindaycount = len(data_df[data_df['DateTime'].dt.date == min_date.date()])
        #maxdaybeforecount = len(data_df[data_df['DateTime'].dt.date == max_date.date()-timedelta(days = 1)])
        if mindaycount != self.day_points:
            data_df = data_df[data_df['DateTime'].dt.date > min_date.date()]
            print(data_df['DateTime'].min())
        
        training_cutoff,val_cutoff,test_cutoff = self.get_split_point(data_df)

        train = data_df[:training_cutoff] 
        val = data_df[training_cutoff : val_cutoff] 
        test = data_df[val_cutoff : test_cutoff] 

        return train,val,test

       


    
