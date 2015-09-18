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
import subprocess
import time
import os
import Queue
import threading

from pykeyboard import PyKeyboard
from PyPDF2 import PdfFileReader


class Presentation():
    """
    This class is the main class for application control
    """

    WAIT_START = 5

    def __init__(self):
        self.pdf = Pdf()
        self.vnc = Vnc()
        self.audio = Audio()
        self.video = Video()
        self.voip = Voip()

    def stop(self):
        """
        This method stops all running presentations
        """
        self.pdf.stop()
        self.vnc.stop()
        self.audio.stop()
        self.video.stop()
        self.voip.stop()

    def is_active(self):
        return self.pdf.is_active() or self.vnc.is_active() or \
               self.audio.is_active() or self.video.is_active() or \
               self.voip.is_active()


class Pdf():
    """
    This Class is for presentation of pdf documents
    standard tool used is evince
    """

    def __init__(self):
        self.process = None
        self.keyboard = PyKeyboard()
        self.filename = ""
        self.path = ""
        self.num_pages = 0

    def start_presentation(self, path, filename):
        """
        This method starts the presentation of PDF documents, standard tool is evince
        :param path:
        :param filename:
        :return: None
        """
        try:
            # get filename and path
            self.path = path
            self.filename = filename
            # start process - filename must be exact file path
            self.process = subprocess.Popen(["evince", os.path.join(path, filename)])
            # get number of pages
            self.num_pages = int(PdfFileReader(open(os.path.join(path, filename), 'rb')).getNumPages())
            # wait until evince is ready
            time.sleep(Presentation.WAIT_START)  # Load time for PDF?
            # maximize
            self.keyboard.press_key(self.keyboard.windows_l_key)
            self.keyboard.tap_key("m")
            self.keyboard.release_key(self.keyboard.windows_l_key)
            # enter presentation mode
            self.keyboard.tap_key(self.keyboard.function_keys[5])
        except:
            return False
        else:
            return True

    def next_page(self):
        """
        This method jumps to next page in pdf reader
        """
        self.keyboard.tap_key(self.keyboard.down_key)

    def previous_page(self):
        """
        This method jumps to last page in pdf reader
        """
        self.keyboard.tap_key(self.keyboard.up_key)

    def first_page(self):
        """
        This method jumps to first page in pdf reader
        """
        self.keyboard.tap_key(self.keyboard.begin_key)

    def last_page(self):
        """
        This method jumps to last page in pdf reader
        """
        self.keyboard.tap_key(self.keyboard.end_key)

    def go_to_page(self, page):
        """
        This method jumps to requested page
        :param = Int
        :return = None
        """
        if int(page) > self.num_pages:
            return
        else:
            # exit the presentation mode
            self.keyboard.tap_key(self.keyboard.escape_key)
            # ctrl+l - go to page focus shortcut
            self.keyboard.press_key(self.keyboard.control_l_key)
            self.keyboard.tap_key("l")
            self.keyboard.release_key(self.keyboard.control_l_key)
            time.sleep(1)
            # Page 210 => int expected 2 , 1 , 0 , Return
            s_page = str(page)
            for x in s_page:
                self.keyboard.tap_key(x)
            self.keyboard.tap_key(self.keyboard.enter_key)
            # enter the presentation mode
            self.keyboard.tap_key(self.keyboard.function_keys[5])

    def get_page_count(self):
        """
        This method returns the number of pages in pdf document
        :return Int
        """
        return self.num_pages

    def stop(self):
        """
        This method stops pdf presentation, if not possible, returns error message
        """
        try:
            if self.process is not None:
                if self.process.poll() is None:
                    self.process.terminate()
                else:
                    return False
            else:
                return False
        except:
            return False
        else:
            return True

    def is_active(self):
        """
        Method (self) test, if it is working
        """
        if self.process is not None:
            if self.process.poll() is None:
                return True
        return False


class Vnc():
    """
    This Class is for presentation user-desktop ,
    standard tool for vnc-connection is ssvnc
    """

    STATUS_NOT_ACTIVE = 0
    STATUS_POLLING = 1
    STATUS_CONNECTING = 2
    STATUS_CONNECTED = 3
    STATUS_ERROR = 4

    def __init__(self):
        # control
        self.process = None
        self.thread = None
        self.keyboard = PyKeyboard()

        # information
        self.active_hostname = ""
        self.active_port = ""

        # ipc
        self.queue = Queue.Queue()
        self._status = 0
        self._message = ""

    def start_connection(self, hostname, port):
        """
        This method starts the presentation by VNC connection, standard tool is ssvnc
        :param hostname: IP address:
        :param port: used ethernet port
        :return: boolean value
        """
        try:
            # remember the hostname and port
            self.active_hostname = hostname
            self.active_port = str(port)

            # start the process
            self.process = subprocess.Popen([os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                          "vnc_fast_start.py"),
                                             hostname,
                                             port],
                                            bufsize=1,
                                            stdout=subprocess.PIPE,
                                            stderr=subprocess.STDOUT)

            # start the thread which is reading stdout
            self.thread = threading.Thread(target=self.enqueue_output)
            self.thread.daemon = True  # thread dies with the program
            self.thread.start()
        except Exception, e:
            return False
        else:
            return True

    def enqueue_output(self):
        """
        worker function for subprocess ipc
        """
        for line in iter(self.process.stdout.readline, b''):
            try:
                self._status, self._message = line.split(";")
                self._status = int(self._status)
            except Exception, e:
                pass

    def status(self):
        """
        Return the status code
        :return:
        """
        return self._status

    def status_text(self):
        if self._status == Vnc.STATUS_NOT_ACTIVE:
            return "Nicht Verbunden"
        elif self._status == Vnc.STATUS_POLLING:
            return "Suche Verbindung"
        elif self._status == Vnc.STATUS_CONNECTING:
            return "Verbindungsaufbau"
        elif self._status == Vnc.STATUS_CONNECTED:
            return "Verbunden"
        elif self._status == Vnc.STATUS_ERROR:
            return "Fehler"
        else:
            return "Unbekannt"

    def message(self):
        """
        Return the last error text
        :return:
        """
        return self._message

    def stop(self):
        """
        This method stops VNC connection
        :return error message, if failed
        """
        try:
            if self.process is not None:
                if self.process.poll() is None:
                    self.process.terminate()
            self._status = Vnc.STATUS_NOT_ACTIVE
        except Exception, e:
            return False
        else:
            return True

    def is_active(self):
        """
        Method (self) test, if it is working
        """
        if self.process is not None:
            if self.process.poll() is None:
                return True
        return False


class Audio():
    """
    This Class is for presentation of music.
    Using VLC keys same as in Video Presentation.
    """

    def __init__(self):
        """
        Constructor
        :return: Audio file handler object
        """
        self.process = None
        self.keyboard = PyKeyboard()
        self.filename = ""
        self.path = ""

    def start_presentation(self, path, filename):
        """
        This method takes care for the start of the audio file.
        Permitted file format is mp3
        :param path: saves path where the file is
        :param filename: filename of the video file
        :return: boolean
        """
        try:
            # get filename and path
            self.path = path
            self.filename = filename
            # start process - filename must be exact file path
            self.process = subprocess.Popen(["vlc", os.path.join(path, filename)])
            # wait until vlc is ready
            time.sleep(Presentation.WAIT_START)
            # maximize
            self.keyboard.press_key(self.keyboard.windows_l_key)
            self.keyboard.tap_key("m")
            self.keyboard.release_key(self.keyboard.windows_l_key)
        except:
            return False
        else:

            return True

    def jump_further(self):
        """
        Jumps to next position in audio file
        :return: None
        """
        self.keyboard.press_key(self.keyboard.control_l_key)
        self.keyboard.tap_key(self.keyboard.right_key)
        self.keyboard.release_key(self.keyboard.control_l_key)

    def jump_back(self):
        """
        Jumps to last position in audio file
        :return: None
        """
        self.keyboard.press_key(self.keyboard.control_l_key)
        self.keyboard.tap_key(self.keyboard.left_key)
        self.keyboard.release_key(self.keyboard.control_l_key)

    def toggle_play(self):
        """
        Method switches pause on/off
        :return: None
        """
        self.keyboard.tap_key(" ")  # Space key

    def toggle_full_screen(self):
        """
        Name is programm. Toggle fullscreen on / off
        Not really necessary, but wayne....
        :return: None
        """
        self.keyboard.tap_key("f")

    def volume_up(self):
        """
        Raises volume of audioplayer
        :return: None
        """
        self.keyboard.press_key(self.keyboard.control_l_key)
        self.keyboard.tap_key(self.keyboard.up_key)
        self.keyboard.release_key(self.keyboard.control_l_key)

    def volume_down(self):
        """
        Lowers volume of audioplayer
        :return: None
        """
        self.keyboard.press_key(self.keyboard.control_l_key)
        self.keyboard.tap_key(self.keyboard.down_key)
        self.keyboard.release_key(self.keyboard.control_l_key)

    def stop(self):
        """
        Stops played audiofile
        :return: None or error msg
        """
        try:
            if self.process is not None:
                if self.process.poll() is None:
                    self.process.terminate()
                else:
                    return False
            else:
                return False
        except:
            return False
        else:
            return True

    def is_active(self):
        if self.process is not None:
            if self.process.poll() is None:
                return True
        return False


class Video():
    """
    This Class is for presentation of Video
    VLC keys:   fullscreen      - f
                Play/Pause      - space
                next file       - n
                previous file   - p
                Volume Up/Down  - Ctrl+Up / Ctrl+Down
                Jump Forward / Backward Hotkeys are empty by default
                 there for need to be set first in the config of VLC
    """

    def __init__(self):
        """
        Constructor
        :return: Video file handler object
        """
        self.process = None
        self.keyboard = PyKeyboard()
        self.filename = ""
        self.path = ""

    def start_presentation(self, path, filename):
        """
        This method takes care for the start of the video file.
        Permitted file formats are avi or mp4.
        :param path: saves path where the file is
        :param filename: filename of the video file
        :return: boolean
        """
        try:
            # get filename and path
            self.path = path
            self.filename = filename
            # start process - filename must be exact file path
            self.process = subprocess.Popen(["vlc", os.path.join(path, filename)])
            # wait until vlc is ready
            time.sleep(Presentation.WAIT_START)
            # maximize
            self.keyboard.press_key(self.keyboard.windows_l_key)
            self.keyboard.tap_key("m")
            self.keyboard.release_key(self.keyboard.windows_l_key)
            self.keyboard.tap_key("f")
        except:
            return False
        else:

            return True

    def jump_further(self):
        """
        Jumps to next position in video file
        :return: None
        """
        self.keyboard.press_key(self.keyboard.control_l_key)
        self.keyboard.tap_key(self.keyboard.right_key)
        self.keyboard.release_key(self.keyboard.control_l_key)

    def jump_back(self):
        """
        Jumps to last position in video file
        :return: None
        """
        self.keyboard.press_key(self.keyboard.control_l_key)
        self.keyboard.tap_key(self.keyboard.left_key)
        self.keyboard.release_key(self.keyboard.control_l_key)

    def toggle_play(self):
        """
        Method switches pause on/off
        :return: None
        """
        self.keyboard.tap_key(" ")  # Space key

    def toggle_full_screen(self):
        """
        Name is programm. Toggle fullscreen on / off
        :return: None
        """
        self.keyboard.tap_key("f")

    def volume_up(self):
        """
        Raises volume of videoplayer
        :return: None
        """
        self.keyboard.press_key(self.keyboard.control_l_key)
        self.keyboard.tap_key(self.keyboard.up_key)
        self.keyboard.release_key(self.keyboard.control_l_key)

    def volume_down(self):
        """
        Lowers volume of videoplayer
        :return: None
        """
        self.keyboard.press_key(self.keyboard.control_l_key)
        self.keyboard.tap_key(self.keyboard.down_key)
        self.keyboard.release_key(self.keyboard.control_l_key)

    def stop(self):
        """
        Stops played videofile
        :return: None or error msg
        """
        try:
            if self.process is not None:
                if self.process.poll() is None:
                    self.process.terminate()
                else:
                    return False
            else:
                return False
        except:
            return False
        else:
            return True

    def is_active(self):
        """
        Selfcheck, if it is running properly
        :return: boolean
        """
        if self.process is not None:
            if self.process.poll() is None:
                return True
        return False


class Voip():
    def __init__(self):
        """
        Constructor
        :return: Video file handler object
        """
        self.process = None
        self.keyboard = PyKeyboard()
        self.filename = ""
        self.url = ""

    def start_voip(self, url=""):
        """
        This method takes care for the start of the video file.
        Permitted file formats are avi or mp4.
        :param path: saves path where the file is
        :param filename: filename of the video file
        :return: boolean
        """
        try:
            # get filename and path
            self.url = url

            # start process - filename must be exact file path
            if url != "":
                self.process = subprocess.Popen(["phone2l", url])
            else:
                self.process = subprocess.Popen(["phone2l"])

            # wait until vlc is ready
            time.sleep(Presentation.WAIT_START)

            # maximize
            self.keyboard.press_key(self.keyboard.windows_l_key)
            self.keyboard.tap_key("m")
            self.keyboard.release_key(self.keyboard.windows_l_key)
        except:
            return False
        else:

            return True

    def stop(self):
        """
        Stops played videofile
        :return: None or error msg
        """
        try:
            if self.process is not None:
                if self.process.poll() is None:
                    self.process.terminate()
                else:
                    return False
                return False
        except:
            return False
        else:
            return True

    def is_active(self):
        """
        Selfcheck, if it is running properly
        :return: boolean
        """
        if self.process is not None:
            if self.process.poll() is None:
                return True
        return False