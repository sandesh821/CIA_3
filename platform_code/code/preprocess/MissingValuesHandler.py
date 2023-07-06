#Copyright (c) Microsoft. All rights reserved.
# Importing all packages required for imputation
import logging
import numpy as np
import pandas as pd
from statsmodels.imputation import mice
import sys
import re
from preprocess import ingestion
from constants import *

# Class for handling missing values algorithm module
class MissingValuesHandler(ingestion):
   
    def __init__(self,data_df,connection_config,preprocess_config):
        super().__init__(connection_config,preprocess_config)
        self.df = data_df
        self.df_cols = data_df.columns

    def reindex_data(self,data_df):
        try : 
            
            data_df[self.source_datetime_col+"Original"] = data_df[self.source_datetime_col]
            data_df = data_df.set_index(pd.DatetimeIndex(data_df[self.source_datetime_col]))
            logging.info("Source dataset count before re-indexing: %i",len(data_df))
            
            if len(self.reindex_cols) > 0:
                nullDates = data_df[data_df[self.reindex_cols[0]].isnull()].index
                for col in self.reindex_cols[1:]:
                    logging.info("Reindexing for {} is completed".format(col))
                    # Identify dates for which values are na
                    nullDates = nullDates.union(data_df[data_df[col].isnull()].index)

                dates = list(set(nullDates.strftime("%Y-%m-%d").tolist())) 
                if len(dates):
                    data_df = data_df.drop(data_df[data_df.index.strftime("%Y-%m-%d").isin(dates)].index)
                    print("After removing NAN dates:", len(data_df))
                    
                    # Reindex the datefield
                    indexRange = pd.to_datetime(pd.date_range(start = str(min(data_df.index)) , end = str(max(data_df.index)) ,freq =self.freq ))
                    indexRange = indexRange[:len(data_df)]
                    data_df = data_df.set_index(pd.DatetimeIndex(indexRange))
                    # # Save the mapping of reindexed date and index
                    data_df["DateTime"] = data_df.index
                    print("Reindexed dataset count:", len(data_df))
                    print("Max date:", max(data_df.index))
                    print("Number of dates dropped:", len(dates))

            return data_df
        except Exception as UnitConversionError:
            logging.error('Error while unit conversion')
            raise UnitConversionError

    # main executing functions
    def missing_main(self):
        """
        Args:
        method : Which algorithm to choose from currently following are the implemented ones \
        """
        # ***************************************
        # trim and reindex the data
        # ***************************************
        df = self.reindex_data(self.df)
        
        return df
        # # saving the file and writing to output path provided