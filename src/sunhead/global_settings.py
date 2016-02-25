"""
Global config values for all application in a package
"""

import tempfile
import os


DEBUG = False
DEBUG_AUTORELOAD_APP = False
USE_DEBUG_TOOLBAR = False
USE_FD_SOCKET = os.environ.get("USE_FD_SOCKET", "False") == "True"
HOST = "0.0.0.0"
PORT = 8080

TMP_DIR = tempfile.gettempdir()

STATS_PRODUCER_ENABLED = True
STATS_PRODUCER_ROUTING_KEY = "runtime_stats"

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'colored': {
            '()': 'colorlog.ColoredFormatter',
            'format': "%(log_color)s%(levelname)-8s%(reset)s %(blue)s[%(name)s:%(lineno)s] %(white)s%(message)s"
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'colored',
        },
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    }
}

STREAM = {}
