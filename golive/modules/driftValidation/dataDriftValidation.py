#Copyright (c) Microsoft. All rights reserved.
# Importing Libraries
import pandas as pd
import numpy as np
from evidently import ColumnMapping
from evidently.report import Report
from evidently.metric_preset import DataDriftPreset
from utilities.azure import blobOperations

class DataDrift:
    def __init__(self, config):
        self.config = config
        self.training_df = blobOperations.getBlobDf(self.config['source_storage_acc_name'],self.config['source_container_name'],self.config['training_file_name'])[1]
        self.training_df = self.training_df[["DateTime"]+self.config["futureCovariates"]+self.config["pastCovariates"]]
        self.test_df = blobOperations.getBlobDf(self.config['storage_acc_name'],self.config['container_name'],self.config['input_file_name'])[1]
        self.num_col_threshold = self.config['num_col_threshold']


    def detect_features_drift(self, df, column_mapping):
        """
        Returns True if Data Drift is detected, else returns False. 
        If get_scores is True, returns scores value (like p-value) for each feature.
        The Data Drift detection depends on the confidence level and the threshold.
        For each individual feature Data Drift is detected with the selected confidence (default value is 0.95).

        """
        # print(df)
        # print(self.training_df)
        data_drift_report = Report(metrics=[DataDriftPreset(num_stattest_threshold=self.num_col_threshold)])
        data_drift_report.run(reference_data=self.training_df, current_data=df, column_mapping=column_mapping)
        report = data_drift_report.as_dict()
        #dict_keys(['number_of_columns', 'number_of_drifted_columns', 'share_of_drifted_columns', 'dataset_drift', 'drift_by_columns'])
        drifts = []
        num_features = column_mapping.numerical_features if column_mapping.numerical_features else []
        dataset_drift = True
        for feature in num_features:
            driftResult = report["metrics"][1]["result"]["drift_by_columns"][feature]
            obj = {
                "feature" : feature,
                "drift_score" : driftResult["drift_score"],
                "drift" : driftResult["drift_detected"]
            }
            drifts.append(obj)
            dataset_drift = dataset_drift and (not driftResult["drift_detected"])
        return drifts, not dataset_drift


    def get_df_drifts(self):
        """  
             Returns True if Data Drift is detected, else returns False. 
             Inputs=treshold value,num_threshold  #     
        """
        lengthOfTestData = len(self.test_df)
        # if lengthOfTestData >= (self.config["lookback"] + self.config['lookahead']):
        # Validate data for past covariates
        df = self.test_df.iloc[:self.config["lookback"]]
        df = df[["DateTime"]+self.config["pastCovariates"]]
        data_columns = ColumnMapping()
        data_columns.numerical_features = self.config["pastCovariates"]

        # Detect drifts in the features
        pastColDrifts, pastColDatasetDrift = self.detect_features_drift(df,data_columns)

        # Validate data for future covariates
        df = self.test_df.iloc[-self.config["lookahead"]:]
        df = df[["DateTime"]+self.config["futureCovariates"]]
        data_columns.numerical_features = self.config["futureCovariates"]
        # Detect drifts in the features
        futColDrifts, futColDatasetDrift = self.detect_features_drift(df,data_columns)

        drifts = pastColDrifts+futColDrifts
        dataset_drift = (not pastColDatasetDrift) and (not futColDatasetDrift)
        print(drifts, (not dataset_drift))
        return drifts, (not dataset_drift)
        # else:
        #     return {"error":"datalength not adequate"}, True