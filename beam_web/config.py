# -*- coding: utf-8 -*-
import logging
import datetime

project_name = "beam"

# Host and Port
HOST = "0.0.0.0"
PORT = 5000

# Runtime
DEBUG = True
TESTING = False
USE_X_SENDFILE = False
SECRET_KEY = "secret"  # import os; os.urandom(24)

# LOGIN
SAFE_ENVIRONMENT = False
# PERMANENT_SESSION_LIFETIME = datetime.timedelta(minutes=100)

# LOGGING
LOGGER_NAME = "%s_log" % project_name
LOG_FILENAME = "/var/tmp/app.%s.log" % project_name
LOG_LEVEL = logging.INFO
LOG_FORMAT = "%(asctime)s %(levelname)s\t: %(message)s"  # used by logging.Formatter

# FOLDER AND UPLOAD
UPLOAD_FOLDER = "static/upload"
ALLOWED_EXTENSIONS = {'pdf', 'avi', 'mp4'}