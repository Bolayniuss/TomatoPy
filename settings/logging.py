# -*- coding: utf-8 -*-
# TomatoPy
from __future__ import print_function, absolute_import, unicode_literals
import os
import logging.config

from .environment import DEBUG


ROLLBAR_TOKEN = os.environ.get("ROLLBAR_TOKEN")


LOGGING = {
    'version': 1,
    'disable_existing_logger': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        }
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'rollbar': {
            'level': 'WARNING',
            'class': 'rollbar.logger.RollbarHandler',
            'access_token': ROLLBAR_TOKEN
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
