# -*- coding: utf-8 -*-
from flask import Flask

# load flask
app = Flask(__name__)
app.config.from_object('config')

# import views
import beam_web.views