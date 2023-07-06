#Copyright (c) Microsoft. All rights reserved.
"""
This module provides utilities for configuring and working with logging.
Any place where logging is required should import this logger and obtain a logger with the
get_logger function.
"""

import logging
import logging.config
from deepmc import config
import os, sys, stat
from datetime import datetime

DEFAULT_LOGGER_FILE_NAME = 'ayana'
DEFAULT_HANDLER = 'file_handler'
JOB_HANDLER = 'job_handler'
BACKUP_COUNT = 7
WHEN = 'midnight'
DELIM = '|'

def get_filepath(logname):
    current_timestamp = datetime.now().strftime('%d_%m_%y_%H_%M_%S')
    file_name = "{}_{}.log".format('Ayana',current_timestamp)
    basename = '{logname}_{basename}.log'.format(basename=file_name, logname=logname)
    log_dir = os.path.join(os.getcwd(), config.LOGS_DIR)

    if not os.path.exists(log_dir):
        print('log path did not exist, creating log folder')
        os.mkdir(log_dir)
        # os.chmod(log_dir, 0o777)
    return os.path.join(os.getcwd(), config.LOGS_DIR, basename)

LOGGING = {
    'version': 1,
    'formatters': {
        'verbose': {
            'format': DELIM.join(["""[%(process)d""", """ %(levelname)-6s""", """%(asctime)s""",
                                  """%(filename)s:%(funcName)s:%(lineno)s]"""]) + """-- %(message)s""",
        }
    },

    'handlers': {
        DEFAULT_HANDLER: {
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'when': WHEN,
            'backupCount': BACKUP_COUNT,
            'level': logging.DEBUG,
            'filename': get_filepath(logname=DEFAULT_LOGGER_FILE_NAME),
            'formatter': 'verbose'
                        },
        'stream_handler': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
            'level': logging.INFO
        }
            },
    'loggers': {
        'default': {
            'handlers': ['file_handler', 'stream_handler'],
            'level': logging.DEBUG,
            'propagate': False
        },
        'generic': {
            'handlers': ['file_handler', 'stream_handler'],
            'level': logging.DEBUG,
            'propagate': False
        }
    }
}
logging.config.dictConfig(LOGGING)

def get_logger(logname):
    logger = logging.getLogger('default')
    logger.propagate = False
    file_name = get_filepath(logname)
    job_handler = logging.FileHandler(filename=file_name)
    job_handler.name = DEFAULT_HANDLER
    job_handler.setFormatter(logging.Formatter(LOGGING['formatters']['verbose']['format']))
    job_handler.setLevel(LOGGING['handlers'][DEFAULT_HANDLER]['level'])
    if (logger.hasHandlers()):
        logger.handlers.clear()
    logger.addHandler(job_handler)
    set_all_permissons_to_log(file_name)
    return logger


def set_all_permissons_to_log(filename):
    '''
    If the log files are present and if the permission is not 777 then make the permission as 777
    else do nothing.
    :return: None
    '''
    filename1 = os.path.join(os.getcwd(), config.LOGS_DIR,filename)
    if os.path.exists(filename1):
        st = os.stat(filename1)
        oct_perm = oct(st.st_mode)
        if oct_perm[-3:] != '777':
            print('changing the permission for logfile')
            # os.chmod(filename1, 0o777)
