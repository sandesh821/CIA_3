from azureml.core import Workspace
from azureml.core import Run
import logging
from masterConfiguration import azureDetails

def getAMLWorkspace():
    logging.info("Fetching AML workspace details")
    logging.info(azureDetails["AMLWORKSPACENAME"])
    try:
        ws = Workspace.from_config()
    except AttributeError as ex:
        logging.error(str(ex))
        current_run = Run.get_context()
        ws = current_run.experiment.workspace
    except Exception as ex:
        logging.info("Reading workspace details from configuration file")
        ws = Workspace.get(name=azureDetails["AMLWORKSPACENAME"],
            subscription_id=azureDetails["SUBSCRIPTIONID"],
            resource_group=azureDetails["RESOURCEGROUP"])
    return ws