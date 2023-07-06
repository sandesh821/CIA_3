import datetime
import logging

import azure.functions as func
from worker import startProcess
 
def main(mytimer: func.TimerRequest) -> None:
    utc_timestamp = datetime.datetime.utcnow().replace(
        tzinfo=datetime.timezone.utc).isoformat()
        
    logging.info('Schedule Pipelines!')
    startProcess()

    logging.info('Trigger function ran at %s', utc_timestamp)
