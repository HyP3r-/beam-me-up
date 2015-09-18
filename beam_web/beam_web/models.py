# -*- coding: utf-8 -*-
import time
import datetime

from flask.ext.login import UserMixin, AnonymousUserMixin


class User(UserMixin):
    """
    This class implements the login - user for session handling
    """

    def __init__(self, username, level, address):
        """
        Constructor
        :param username:
        :param password:
        :return: user object
        """
        self.id = username + "-" + str(time.time())
        self.username = username
        self.level = level
        self.address = address
        self.last_seen = time.time()

    def is_lecturer(self):
        return True if self.level == UserDatabase.USER_LECTURER else False

    def is_guest(self):
        return True if self.level == UserDatabase.USER_GUEST else False


class BeamAnonymousUserMixin(AnonymousUserMixin):
    def __init__(self):
        super(BeamAnonymousUserMixin, self).__init__()
        self.level = UserDatabase.USER_ANONYMOUS

    def is_lecturer(self):
        return False

    def is_guest(self):
        return False


class UserDatabase():
    lecturers_database = [("dozent", "secret"), ("dozent-01", "secret")]
    user_database = list()
    USER_ANONYMOUS = 0
    USER_LECTURER = 2
    USER_GUEST = 1

    def __init__(self, safe_environment):
        self.safe_environment = safe_environment

    def login_lecturer(self, username, password, address):
        # get the login type and check if login is possible
        for l_username, l_password in self.lecturers_database:
            if l_username == username and l_password == password:
                # username and password is correct
                # first remove all other lecturers
                for user in self.user_database:
                    if user.is_lecturer() and user.username == username:
                        self.user_database.remove(user)
                # return the new user object
                return self.create_user(username, UserDatabase.USER_LECTURER, address)
        return None

    def login_guest(self, username, password, address):
        # check if the given username is already logged in
        for user in self.user_database:
            if user.username == username:
                return None

        # check if the given username is a lecturer username
        for l_username, l_password in self.lecturers_database:
            if l_username == username:
                return None

        # get the login type and check if login is possible
        return self.create_user(username, UserDatabase.USER_GUEST, address)

    def create_user(self, username, level, address):
        user = User(username, level, address)
        self.user_database.append(user)
        return user

    def logout_user(self, user_id):
        for user in self.user_database:
            if user.id == user_id:
                self.user_database.remove(user)

    def get(self, user_id):
        for user in self.user_database:
            if user.id == user_id:
                return user
        return None

    def auto_login(self, user, address):
        # auto login in safe environment
        if self.safe_environment and user.level == UserDatabase.USER_ANONYMOUS:
            # search for lecturers
            for u in self.user_database:
                if u.is_lecturer():
                    return None

            # if no lecturer found log in
            return self.create_user(self.lecturers_database[0][0],
                                    UserDatabase.USER_LECTURER,
                                    address)

    def process_sessions(self, user, presentation):
        # cleanup lecturer
        if not presentation.is_active():
            for user in self.user_database:
                if user.is_lecturer():
                    if time.time() - user.last_seen > datetime.timedelta(minutes=10).seconds:
                        self.user_database.remove(user)

        # cleanup guests
        for user in self.user_database:
            if user.is_guest():
                if time.time() - user.last_seen > datetime.timedelta(minutes=90).seconds:
                    self.user_database.remove(user)

        # refresh user
        if user.is_guest() or user.is_lecturer():
            user.last_seen = time.time()
