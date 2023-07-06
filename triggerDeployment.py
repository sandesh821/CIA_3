#Copyright (c) Microsoft. All rights reserved.
import sys
import os
import shutil
import json
import logging
from utilities import config
currentDir = os.path.dirname(os.path.abspath(os.path.join(__file__,"../..")))
sys.path.insert(0,currentDir)
from utilities.azure import blobOperations
from golive.MlOpsAutomation.scripts import prepareConfigurations
from deployment import runDeploymentManager

data = {
        "experimentsetid":56,
        "experimentsetname" : "solarewbrown",
        "fileUpload" : False,
        "type": "best"
    }

# Setup Function app and generate docker image
prepareConfigurations.setup(data, data["type"])

# Setup and deploy go live AKS module
runDeploymentManager.triggerDeploymentManager(data, data["type"])