# -*- coding: utf-8 -*-
# TomatoPy
from __future__ import print_function, absolute_import, unicode_literals
import os
import logging.config

from .environment import DEBUG, ENV_NAME


ROLLBAR_TOKEN = os.environ.get("ROLLBAR_TOKEN")

LOGGING = {
    'version': 1,
    'disable_existing_logger': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(message)s'
        }
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
        'rollbar': {
            'level': 'WARNING',
            'class': 'rollbar.logger.RollbarHandler',
            'access_token': ROLLBAR_TOKEN,
            'formatter': 'verbose',
            'environment': ENV_NAME
        }
    },
    'loggers': {
        '': {
            'level': 'INFO' if not DEBUG else 'DEBUG',
            'handlers': ['console'] + ['rollbar'] if ROLLBAR_TOKEN else []
        }
    }
}

logging.config.dictConfig(LOGGING)
