# -*- coding: utf-8 -*-
# TomatoPy
from __future__ import print_function, absolute_import, unicode_literals
import os
import dotenv


def is_true(v):
    return v == 1 or v is True or (isinstance(v, str) and v.lower() in ['y', 'yes', 'true'])

environ_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")

if not os.path.exists(environ_file):
    raise EnvironmentError("No .env file found")
dotenv.load_dotenv(environ_file)

DEBUG = os.environ.get("DEBUG", False)

DEPLOYMENT_NAME = os.environ.get("DEPLOYMENT_NAME", "default_name")
ENV_TYPE = "development" if DEBUG else "production"
ENV_NAME = DEPLOYMENT_NAME + "_" + ENV_TYPE
