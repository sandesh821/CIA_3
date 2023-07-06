import pandas as pd
import numpy as np
import math
from sklearn.metrics import mean_squared_error, mean_absolute_error
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from dboperations.dboperations import executeStoredProcedure


class AggregatorQuery:
    def __init__(self, func, exp_sets=None, exp_names=None, start=False, end=False, needAll=False):
        """
        Initialize the AggregatorQuery class

        Parameters:
            - func (function): function to apply to the error list
            - exp_sets (list): list of experiment sets
            - exp_names (list): list of experiment names
            - start (bool): start time for the query
            - end (bool): end time for the query
            - needAll (bool): flag indicating if all data should be returned
        """
        self.exp_sets = self.input_check(exp_sets)
        self.func = func
        self.start_time = start
        self.end_time = end
        self.exp_names = self.input_check(exp_names)
        self.needAll = needAll
        self.comp_list = self._get_exp_names_and_error_dict()
        self.error_list = self.err()
        self.agglist = self.agglist()

        all_exp_sets = self.get_all_exp_sets()

        if exp_sets:     
            if not set(self.exp_sets).issubset(all_exp_sets):
                raise ValueError("ExperimentSet name/s not found!")

        all_exp_names = self._get_all_names()

        if exp_names:
            if not set(self.exp_names).issubset(all_exp_names):
                raise ValueError("Experiment name/s not found!")

    # exception handling
    def input_check(self, value):
        """
        Check the input value for correct type

        Parameters:
            - value (list or str): value to check

        Returns:
            - list: value cast to list if input was str
        """
        if value:
            if not isinstance(value, list):
                if isinstance(value, str):
                    return [value]
                else:
                    raise TypeError("Input must be a list or a string")
        return value

    # Get all experiment sets
    def get_all_exp_sets(self):
        """
        Get all available experiment sets

        Returns:
            - list: list of experiment sets
        """
        all_exp_sets = executeStoredProcedure(procName="getAllExperimentSet", paramList=None, params=None, SchemaName="dbo", isGetResult=2)
        return all_exp_sets["ExperimentSet"].tolist()

    # Get all experiments
    def _get_all_names(self):
        """
        Get all available experiments

        Returns:
            - list: list of experiments
        """
        all_exp_names = executeStoredProcedure(procName="getAllExperiment", paramList=None, params=None, SchemaName="dbo", isGetResult=2)
        return all_exp_names["Experiment"].tolist()

    # Get all finished experiment names from an experiment set
    def _get_exp_names(self, exp_set):
        """
        Get all finished experiment names from a given experiment set

        Parameters:
            - exp_set (str): experiment set name

        Returns:
            - list: list of finished experiment names
        """
        exp_names_list = executeStoredProcedure("usp_getExpNames","@ExperimentSet = ?, @RunStatus = ?", ("{}".format(exp_set),"Finished"),"dbo",2)
        return exp_names_list["Experiment"].tolist()

    # returns the latest successfully run internalRunID from an experiment
    def _get_run_ids(self, exp_name):
        """
        Get the latest successfully run internalRunID from a given experiment

        Parameters:
            - exp_name (str): experiment name

        Returns:
            - int: internal run ID
        """
        run_id_list = executeStoredProcedure("usp_getInternalRunID","@Experiment = ?, @RunStatus = ?", ("{}".format(exp_name),"Finished"),"dbo",1)
        return run_id_list[0] 

    # fetch the list of error values from a given set of ExperimentSet, Experiment and internalRunID
    def get_error(self, exp_set, exp_name, irunid):
        """
        Get the list of error values from a given set of ExperimentSet, Experiment and internalRunID

        Parameters:
            - exp_set (str): experiment set name
            - exp_name (str): experiment name
            - irunid (int): internal run ID

        Returns:
            - list: list of error values
        """
        error = executeStoredProcedure("usp_getErrors", "@ExperimentSet = ?, @Experiment = ?, @InternalRunId = ?", ("{}".format(exp_set), "{}".format(exp_name), "{}".format(irunid)),"dbo",2)
        return error["Error"].tolist()

    # returns a list of set containing ExperimentSet, Experiment and internalRunID
    def _get_exp_names_and_error_dict(self) -> list:
        """
        Get a list of sets containing ExperimentSet, Experiment and internalRunID

        Returns:
            - list: list of sets
        """
        comp_list = []

        if self.exp_sets  is None and self.exp_names is not None:
            for exp_name in self.exp_names:
                expset_runid = executeStoredProcedure("usp_getExperimentSetAndInternalRunid", "@Experiment = ?, @RunStatus = ?", ("{}".format(exp_name), "Finished"),"dbo",2)
                for i, row in expset_runid.iterrows():
                    comp_list.append((expset_runid["ExperimentSet"].values.tolist()[0], exp_name, expset_runid["InternalRunID"].values.tolist()[0]))      
        
        elif self.exp_names is None and self.exp_sets is not None:
            for exp_set in self.exp_sets:
                exp_names = self._get_exp_names(exp_set)         
                for exp_name in exp_names:
                    run_id =  self._get_run_ids(exp_name)
                    comp_list.append((exp_set,exp_name, run_id))
                    
        elif self.needAll:
        #self.exp_names == None and self.exp_sets == None
            exp_sets = self.get_all_expSets()
            for exp_set in exp_sets:
                exp_names = self._get_exp_names(exp_set)         
                for exp_name in exp_names:
                    run_id =  self._get_run_ids(exp_name)
                    comp_list.append((exp_set,exp_name, run_id))


        else:
            for exp_set in self.exp_sets:
                exp_names_list = self._get_exp_names(exp_set)
                for i in self.exp_names:
                    if i in exp_names_list:
                        run_id =  self._get_run_ids(i)
                        comp_list.append((exp_set, i, run_id))
        
        
        return  comp_list


    def err(self):
        """
        Get the list of error values for a list of (experimentSet, Experiment, internalRunID) tuples
        
        :return: list of error values
        """
        error_list = []
        for elements in self.comp_list:
            error_list.append(self.get_error(elements[0], elements[1], elements[2]))
        return error_list

    def apply_map(self):
        """
        Apply the specified function to the list of error values and round the results to 2 decimal places
        
        :return: list of rounded values
        """
        map_values = list(map(self.func, [error for error in self.error_list]))
        return [round(x, 2) for x in map_values]

    def agglist(self):
        """
        Combine the aggregated result with its respective (experimentSet, Experiment, internalRunID) into a single list
        
        :return: list of tuples
        """
        maplist = self.apply_map()
        return [(run_pair[0], run_pair[1], run_pair[2], value) for run_pair, value in zip(self.comp_list, maplist)]


def get_MAE(errors):
    """
    Calculate the mean absolute error for a list of errors
    
    :param errors: list of errors
    :type errors: list
    :return: mean absolute error
    """
    absolute_errors = [abs(error) for error in errors]
    mae = sum(absolute_errors) /len(absolute_errors)
    return mae

def get_rmse(errors):
    """
    Calculate the root mean squared error for a list of errors
    :param errors: list of errors
    :type errors: list
    :return: root mean squared error
    """
    from math import sqrt
    return sqrt(sum([error**2 for error in errors]) / len(errors))


if __name__ == '__main__':
    #c = AggregatorQuery(exp_sets = ["DeepMCAggregator"], func = get_rmse)
    #c = AggregatorQuery(exp_names = ["experiment_aggregator"], func = get_rmse)
    c = AggregatorQuery(exp_sets = ["DeepMCAggregator"], exp_names = ["experiment_aggregator", "experiment_aggregator1"], func = get_rmse)
    #c = AggregatorQuery(exp_sets = ["DeepMCAggregator"], exp_names = ["experiment_aggregator"], func = get_rmse)
    #print(c.comp_list) 
    print(c.agglist)
    

