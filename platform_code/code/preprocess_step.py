#Copyright (c) Microsoft. All rights reserved.
import os
from azureml.pipeline.steps import PythonScriptStep

def data_preprocess_step(run_config,preprocess_directory,splitfiles_ds, compute_target,preprocess_config,connection_config):

    step = PythonScriptStep(name="preprocess",
                         script_name="preprocess.py", 
                         arguments=["--connection-config",connection_config,"--preprocess-config",preprocess_config,'--output-data', splitfiles_ds],
                         outputs=[splitfiles_ds],
                         compute_target=compute_target, 
                         source_directory=preprocess_directory,
                         runconfig=run_config,
                         allow_reuse=True)
    return step


