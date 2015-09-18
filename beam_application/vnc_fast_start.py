#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Beam Application
# Copyright (C) 2015 Andreas Fendt, Martin Demharter and Yordan Pavlov
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
    VNC Fast Start
    Waits during a timeout period for a port 5900 on a given IP
    to be open. Then it connects the VNC client to it.
    If the timeout period passes it exits.

    Usage: python(3) vnc_fast_start.py [ip] [port]

    Print Output for Status of Connection explained:
              0 - for Waiting on IP/Port
              1 - Port Open / Starting connection
              2 - Connection established
              3 - Error. Problems with Connecting.
              Comment: Should there be a Code for EXIT without an Error?
"""

import socket
import sys
import time
import subprocess
import signal
from pykeyboard import PyKeyboard


class VncFastStart():
    """
    VncFastStart System for connecting to vnc server
    with automatic polling
    """

    STATUS_NOT_ACTIVE = 0
    STATUS_POLLING = 1
    STATUS_CONNECTING = 2
    STATUS_CONNECTED = 3
    STATUS_ERROR = 4

    def __init__(self):
        # ip should be passed as a Starting Argument to the program maybe even the Port
        self.ip = str(sys.argv[1])
        self.port = int(sys.argv[2])
        self.timeout = 60

        # Creating Socket, just one is needed.
        self.socket_vnc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # variables
        self.keyboard = PyKeyboard()
        self.process = None

        # signals
        signal.signal(signal.SIGTERM, self.signal_term_handler)

    def signal_term_handler(self, signum, frame):
        """
        Handler for system signals
        """
        if signum == signal.SIGTERM or signum == signal.SIGKILL:
            try:
                if self.process is not None:
                    if self.process.poll() is None:
                        self.process.kill()

            except Exception, e:
                pass
            sys.exit(0)

    def start_connection(self):
        try:
            # stat the subprocess
            self.process = subprocess.Popen(["beam_vnc",
                                             "-viewonly",
                                             "-encodings", "Zlib",
                                             "{0}:{1}".format(self.ip, self.port)],
                                            bufsize=1,
                                            stdout=subprocess.PIPE,
                                            stderr=subprocess.STDOUT)
        except Exception, e:
            self.write(str(VncFastStart.STATUS_ERROR) + ";" + str(e.message).strip())
            return

        # wait until ready
        time.sleep(2)

        # maximize
        self.keyboard.press_key(self.keyboard.windows_l_key)
        self.keyboard.tap_key("m")
        self.keyboard.release_key(self.keyboard.windows_l_key)

        # send that the system has started the program
        self.write(str(VncFastStart.STATUS_CONNECTED) + ";")

        # loop line by line
        for line in iter(self.process.stdout.readline, b''):
            # search for fail or error and print it
            if "error" in line or "fail" in line:
                pass  # self.write(str(VncFastStart.STATUS_ERROR) + ";" + str(line).strip())

    def tcp_port_open(self):
        try:
            result = self.socket_vnc.connect_ex((self.ip, self.port))
            if result == 0:
                self.socket_vnc.close()
                return True
            else:
                return False
        except:
            return False

    def start_polling(self):
        # send that the system is starting to connect
        self.write(str(VncFastStart.STATUS_POLLING) + ";")
        for x in range(0, self.timeout):
            if self.tcp_port_open():
                # send that the system is trying to connect
                self.write(str(VncFastStart.STATUS_CONNECTING) + ";")
                time.sleep(0.5)

                # start the connection
                self.start_connection()

                # exit the program
                exit(0)
            else:
                time.sleep(5)

    def write(self, text):
        print(text)
        sys.stdout.flush()


if __name__ == "__main__":
    VncFastStart().start_polling()

