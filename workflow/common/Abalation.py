#Copyright (c) Microsoft. All rights reserved.
import itertools
import pandas as pd
from workflow.common.config import EXPERIMENTS_START_TAG

class Abalation:
    def __init__(self, all_column_tag_dict, num_new_experiments, last_experiment_number, algorithms, features_of_completed_experiments):
        self._experiment_ext = f"{EXPERIMENTS_START_TAG}"
        self._all_column_tag_dict = all_column_tag_dict
        self._num_new_experiments = num_new_experiments
        self._last_experiment_number = last_experiment_number
        self._algorithms = algorithms
        self._features_of_completed_experiments = features_of_completed_experiments


    def _get_completed_experiments(self):
        return  [ self._casting(val) for val in self._features_of_completed_experiments]

    def _casting(self,val):
        return tuple(sorted(list(val)))

    def overall_feature_combinations(self, permanent_features=[], remove_completed=True):
        features_list = []
        for k in range(len(permanent_features), len(self._all_column_tag_dict.keys()) + 1):
            if k == 0:
                continue
            your_output = list(self._casting(combination) for combination in itertools.combinations(self._all_column_tag_dict.keys(), k) if
                               all(element in combination for element in permanent_features))
            features_list.extend(your_output)
        if self._num_new_experiments > len(features_list):
            self._num_new_experiments = len(features_list)
        if remove_completed:
            completed_experiments_features = self._get_completed_experiments()
            return self._assign_experiment_nums(self._sort_experiments(list(set(features_list).difference(completed_experiments_features)))[:self._num_new_experiments])
        else:
            return self._assign_experiment_nums(self._sort_experiments(features_list)[:self._num_new_experiments])

    def _sort_experiments(self, features_list):
        feature_list_d = {}
        for features in features_list:
            feature_list_d[features] = len([self._all_column_tag_dict[feature] for feature in features if self._all_column_tag_dict[feature]!='']) / len(features)
        sorted_features_list = sorted(feature_list_d.items(), key=lambda x: x[1])[::-1]
        sorted_features_list = [feature[0] for feature in sorted_features_list]
        return sorted_features_list


    def _assign_experiment_nums(self, sorted_features_list):
        last_experiment_number = self._last_experiment_number

        features_list_dict = []
        for features in sorted_features_list:
            for algorithm in self._algorithms:
                last_experiment_number += 1
                features_list_dict.append([self._experiment_ext + str(last_experiment_number), algorithm, list(features)])
        return features_list_dict

if __name__ == '__main__':
    file_col_tag_dict = {'file1_col1':'tag1', 'file1_col2':'tag2', 'file1_col3':'', 'file2_col1':'tag1', 'file2_col2':'tag2', 'file3_col1':'tag1'}
    features_of_completed_experiments = [('file1_col1', 'file1_col2', 'file2_col1', 'file3_col1'), ('file1_col1', 'file1_col3', 'file2_col1', 'file3_col1')]
    algorithms = ["DeepMC", "TFT"]

    al = Abalation(file_col_tag_dict, 30, 10, algorithms, features_of_completed_experiments)
    permanent_features = []#tuple(sorted(['file3_col1', 'file2_col1', "file1_col1"]))
    experiments_dict = al.overall_feature_combinations(permanent_features)
