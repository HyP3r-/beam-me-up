# -*- coding: utf-8 -*-
from wtforms import *


class LoginForm(Form):
    """
    This method transports the login data from html to python
    :param: formular from html, with login data
    """
    username = StringField("Username", validators=(validators.required(),))
    level = StringField("level")
    password = PasswordField("Password")


class ConnectionControlForm(Form):
    """
    This method transports the connection control data from html to python
    :param: formular from html, with connection control data
    """
    action = StringField(validators=(validators.required(),))
    param = StringField(validators=(validators.required(),))


class PresentationControlForm(Form):
    """
    This method transports the presentation control data from html to python
    :param: formular from html, with control data data
    """
    action = StringField(validators=(validators.required(),))
    param = StringField(validators=(validators.required(),))


class ProjectorControlForm(Form):
    """
    This method transports the presentation control data from html to python
    :param: formular from html, with control data data
    """
    action = StringField(validators=(validators.required(),))
    param = StringField(validators=(validators.required(),))

