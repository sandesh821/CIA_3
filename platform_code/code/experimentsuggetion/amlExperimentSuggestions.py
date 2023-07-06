from azureml.core import Workspace, Datastore, Dataset
import pandas as pd
#connection establishment from parent directory dboperations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


#fetching all results csv from blob in tabular format
def blob_data_fetch(exp_name):
     
    ws = Workspace.from_config()
    datastore = ws.get_default_datastore() 

    data = Dataset.Tabular.from_delimited_files(path = [(datastore, "outputs/{}/**/results.csv".format(exp_name))],header='ALL_FILES_HAVE_SAME_HEADERS',  validate=False, infer_column_types= False)
 
    data = data.to_pandas_dataframe()
    return(data)
