#Copyright (c) Microsoft. All rights reserved.
import sys
import os

currentDir = os.path.dirname(os.path.abspath(os.path.join(__file__, "../..")))
sys.path.insert(0, currentDir)
print("directory done")
from deployment import runDeploymentManager
print("import1")
from workflow.common import getdata
print("import2")


def main():
    experimentsetid = get_experimentsetid()
    experimentsetname = get_experimentsetname()
    fileupload = get_fileupload()
    deployment_type = get_deployment_type()

    data = {
        "experimentsetid": experimentsetid,
        "experimentsetname": experimentsetname,
        "fileUpload": fileupload,
        "type": deployment_type
    }

    print("Data:", data)  # Print the data dictionary

    # Setup and deploy go live AKS module
    runDeploymentManager.triggerDeploymentManager(data, data["type"])


def get_experimentsetid():
    return int(sys.argv[1])  # Command-line argument for experimentsetid


def get_experimentsetname():
    return sys.argv[2]  # Command-line argument for experimentsetname


def get_fileupload():
    return sys.argv[3].lower() == 'true'  # Command-line argument for fileUpload as boolean


def get_deployment_type():
    return sys.argv[4]  # Command-line argument for deployment type


if __name__ == "__main__":
    print("Started .py")
    main()
