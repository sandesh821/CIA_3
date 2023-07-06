#Copyright (c) Microsoft. All rights reserved.
# Importing Libraries
import pandas as pd
import numpy as np
from evidently import ColumnMapping
from evidently.report import Report
from evidently.metric_preset import DataDriftPreset,TargetDriftPreset
from evidently.metrics import *
from evidently.tests import *
from utilities.dboperations.dboperations import executeStoredProcedure
from utilities.azure import blobOperations

class TargetDrift:
    def __init__(self,config):
        self.config = config
        print(self.config['source_storage_acc_name'],self.config['source_container_name'])
        print(self.config['training_file_name'])
        print(self.config['input_file_name'])
        self.training_df = blobOperations.getBlobDf(self.config['source_storage_acc_name'],self.config['source_container_name'],self.config['training_file_name'])[1]
        self.training_df = self.training_df[self.config["targetDriftColList"]]
        self.test_df = blobOperations.getBlobDf(self.config['storage_acc_name'],self.config['container_name'],self.config['input_file_name'])[1]
        self.drift_share= self.config['drift_share']
        self.colList = self.config["targetDriftColList"]


    def detect_features_drift(self, column_mapping, get_scores=False):
        """
        Returns True if Data Drift is detected, else returns False. 
        If get_scores is True, returns scores value (like p-value) for each feature.
        The Data Drift detection depends on the confidence level and the threshold.
        For each individual feature Data Drift is detected with the selected confidence (default value is 0.95).

        """
        target_drift_report = Report(metrics=[DataDriftPreset(num_stattest_threshold=self.drift_share)])  
        target_drift_report.run(reference_data=self.training_df, current_data=self.test_df, column_mapping= column_mapping)

        report = target_drift_report.as_dict()
        drifts = report["metrics"][1]["result"]["drift_by_columns"]["Prediction"]     
        return drifts


    def get_df_drifts(self):
        """  
             Returns True if Data Drift is detected, else returns False. 
             Inputs=treshold value,num_threshold  #  
             Sample output: {'column_name': 'Prediction', 'column_type': 'num', 'stattest_name': 'K-S p_value', 'stattest_threshold': 1.5, 'drift_score': 6.674724060114783e-22, 'drift_detected': True, 'current': {'small_distribution': {'x': [8074.322265625, 8325.0359375, 8575.749609375, 8826.46328125, 9077.176953125, 9327.890625, 9578.604296875, 9829.31796875, 10080.031640625, 10330.7453125, 10581.458984375], 'y': [0.0019943068770868102, 0.00016619223975723542, 0.00033238447951446836, 0.00033238447951447085, 0.00016619223975723418, 0.00016619223975723418, 0.00033238447951447085, 0.00016619223975723418, 0.0, 0.00033238447951446836]}}, 'reference': {'small_distribution': {'x': [-274.176025390625, 995.4149169921875, 2265.005859375, 3534.5968017578125, 4804.187744140625, 6073.7786865234375, 7343.36962890625, 8612.960571289062, 9882.551513671875, 11152.142456054688, 12421.7333984375], 'y': [0.00041570694950550456, 7.001380202197971e-05, 5.1416385859891345e-05, 2.516121010164896e-05, 5.3604317173078224e-05, 4.266466060714389e-05, 6.454397373901255e-05, 5.469828282967165e-05, 4.375862626373732e-06, 5.469828282967165e-06]}}}   
        """
        data_columns = ColumnMapping()
        data_columns.numerical_features = self.colList
        
        drifts = self.detect_features_drift(column_mapping=data_columns)
        print(drifts)
        return drifts
    