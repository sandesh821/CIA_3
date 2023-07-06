import os
import pandas as pd
import io
import requests
import ast
from amlExperimentSuggestions import blob_data_fetch
from dboperations.dboperations import executeStoredProcedure


class ExperimentSuggestion:
    def __init__(self, exp_name: str):
        """
        Initialize the ExperimentSuggestion class with the experiment name as an input.
        The input must be a string.

        Parameters:
            exp_name (str): name of the experiment

        Returns:
            None
        """
        self.exp_name = exp_name if isinstance(exp_name, str) else None
        if self.exp_name is None:
            raise TypeError("Input must be a string")
        self.p_rank = None
        self.f_rank = None
        self.p_score = None
        self.f_score = None
        self.best_past_covariate = None
        self.best_future_covariate = None

        # getting list of all experiment names
        df_results = executeStoredProcedure(
            procName="usp_get_expList",
            paramList=None,
            params=None,
            SchemaName="dbo",
            isGetResult=2,)
        self.all_exp = df_results["Experiment"].tolist()

        if self.exp_name is None:
            raise TypeError("Input must be a string")

        if exp_name not in self.all_exp:
            raise ValueError("Experiment name not found!")

    # passing the experiment name as attribute
    # generates weights for each run based on respective RMSE value
    def get_df(self, exp_name: str):
        """
        Returns a dataframe of the experiment with additional columns of "weights"
        based on the RMSE value of the respective run.

        Parameters:
            exp_name (str): name of the experiment

        Returns:
            df (pd.DataFrame) : dataframe of the experiment
        """
        df = blob_data_fetch(exp_name)
        df["Future Covariates"] = df["Future Covariates"].apply(lambda s: set(ast.literal_eval(s)))
        df["Past Covariates"] = df["Past Covariates"].apply(lambda s: set(ast.literal_eval(s)))
        df["RMSE"] = df["RMSE"].astype(str).astype(float)
        df["weights"] = round(1 / df["RMSE"], 2)
        return df

    # records the weight-score distribution of each covariate
    def dist(self, x: str, exp_name: str):
        """
        Returns a dictionary of weight-score distribution of each covariate
        
        Parameters:
            x (str) : column name of the covariates in the dataframe
            exp_name (str): name of the experiment
        
        Returns:
            l (dict) : weight-score distribution of each covariate
        """
        df = self.get_df(exp_name)
        l = {}
        for _, row in df.iterrows():
            for item in list(row[x]):
                if item in l:
                    l[item].append(row["weights"])
                else:
                    l[item] = []
                    l[item].append(row["weights"])
        return l

    # calculates average score based on the weight-score distribution
    def score(self, x: dict):
        """
        Returns a dictionary of average score based on the weight-score distribution
        
        Parameters:
            x (dict) : weight-score distribution of each covariate
        
        Returns:
            y (dict) : average score of each covariate
        """
        y = x.copy()
        for i in x:
            y[i] = round(sum(y[i]) / len(y[i]), 3)
        return y

    # select the best Covariate
    def best_covariate(self, x: dict):
        """
        Returns the best covariate based on the average score
        
        Parameters:
            x (dict) : average score of each covarite
            Returns:
            best (str) : best covariate
        """
        mx = -1
        best = ""
        for i in x:
            if x[i] > mx:
                mx = x[i]
                best = i
        return best

    def run(self):
        """
        Executes the ExperimentSuggestion class by calculating the weight-score distribution 
        of each past and future covariate, average score of each past and future covariate, 
        and the best past and future covariate.
        
        Parameters:
            None
        
        Returns:
            Tuple: containing the weight-score distribution of past and future covariates, 
            average score of past and future covariates, and best past and future covariates.
        """
        exp_name = self.exp_name
        self.p_rank = self.dist("Past Covariates", exp_name)
        self.f_rank = self.dist("Future Covariates", exp_name)
        self.p_score = self.score(self.p_rank)
        self.f_score = self.score(self.f_rank)
        self.best_past_covariate = self.best_covariate(self.p_score)
        self.best_future_covariate = self.best_covariate(self.f_score)
        return (
            self.p_rank,
            self.f_rank,
            self.p_score,
            self.f_score,
            self.best_past_covariate,
            self.best_future_covariate,
        )


if __name__ == "__main__":
    test = ExperimentSuggestion("experiment1_solar_team4")
    p_rank, f_rank, p_score, f_score, best_past_covariate, best_future_covariate = test.run()
    print(p_rank)
    print(f_rank)
    print(p_score)
    print(f_score)
    print(best_past_covariate)
    print(best_future_covariate)
