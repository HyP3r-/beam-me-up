#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Beam CLI
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
import cmd
import os
import datetime

from beam_application.presentation import Presentation
import config



# TODO those functions are nearly the same as in beam_web
# TODO get_upload_folder has to be improved

def get_upload_folder():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "../beam_web",
                        config.UPLOAD_FOLDER)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in config.ALLOWED_EXTENSIONS


def get_human_size(nbytes):
    suffixes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    if nbytes == 0:
        return '0 B'
    i = 0
    while nbytes >= 1024 and i < len(suffixes) - 1:
        nbytes /= 1024.
        i += 1
    f = ('%.2f' % nbytes).rstrip('0').rstrip('.')
    return '%s %s' % (f, suffixes[i])


class BeamCli(cmd.Cmd):
    """Command processor for beam"""

    def __init__(self, completekey='tab', stdin=None, stdout=None):
        cmd.Cmd.__init__(self, completekey, stdin, stdout)
        self.pres = Presentation()

    """
        Video
    """

    def do_vs(self, line):
        """
        Starts Video
        vs [FileName]
        """
        if line:
            print("Starting Video File:", line)
            self.pres.video.start_presentation(get_upload_folder(), line)

        else:
            print('please input FilePath FileName')

    def do_vc(self, line):
        """
        Close Video
        """
        print("Impl. Stop Video: stop(self)")
        self.pres.video.stop()

    def do_vp(self, line):
        """
        Pause/Play Video
        """
        print("Impl. Stop Video: toggle_play()")
        self.pres.video.toggle_play()

    def do_vf(self, line):
        """
        Video Forward
        """
        print("Impl. Video Forward self.pres.video.jump_further()")
        self.pres.video.jump_further()

    def do_vb(self, line):
        """
        Video Backward
        """
        print("Impl. Video Backword self.pres.video.jump_back():")
        self.pres.video.jump_back()

    """
    Audio
    """

    def do_as(self, line):
        """
        Starts audio (in the upload folder)
        as [Filename]
        """
        if line:
            print("Starting audio File:", line)
            self.pres.audio.start_presentation(get_upload_folder(), line)
        else:
            print('please input FilePath FileName')

    def do_ac(self, line):
        """
        Close audio
        """
        print("Impl. Stop audio: stop(self)")
        self.pres.audio.stop()

    def do_ap(self, line):
        """
        Pause/Play audio
        """
        print("Impl. Stop audio: toggle_play()")
        self.pres.audio.toggle_play()

    def do_af(self, line):
        """
        audio Forward
        """
        print("Impl. audio Forward pres.audio.jump_further()")
        self.pres.audio.jump_further()

    def do_ab(self, line):
        """
        audio Backward
        """
        print("Impl. audio Backword pres.audio.jump_back():")
        self.pres.audio.jump_back()

    """
        PDF
    """

    def do_ps(self, line):
        """
        Open PDF File
        ps [Filename]
        """
        if line:
            print("Starting PDF File", line)
            self.pres.pdf.start_presentation(get_upload_folder(), line)
        else:
            print('please input FilePath FileName')

    def do_pc(self, line):
        """
        PDF Close
        """
        print("Pdf Close")
        self.pres.pdf.stop()

    def do_pn(self, line):
        """
        PDF next page
        """
        print("Pdf next page")
        self.pres.pdf.next_page()

    def do_pp(self, line):
        """
        PDF previous page
        """
        print("Pdf previous page")
        self.pres.pdf.previous_page()

    def do_pg(self, line):
        """
        PDF go to page
        pn [PageNumber]
        """
        try:
            float(line)
            print("Pdf go to page ", line)
            self.pres.pdf.go_to_page(line)
        except ValueError:
            print("Not a number")

    """
        VNC
    """

    def do_cs(self, line):
        """
        Connects VNC Client to a Server
        cs [server]
        """
        if line:
            print("Connect VNC Client to ", line)
            self.pres.vnc.stop()
            self.pres.vnc.start_connection(line, "5900")
        else:
            print('please input Valid VNC Server Address')

    def do_cc(self, line):
        """
        VNC close
        """
        print("VNC Close")
        self.pres.vnc.stop()

    """
        Beamer
    """

    # def do_bm(self, line):
    # """
    # Beamer Mute
    # """
    # print("Beamer Mute")
    #
    # def do_bs(self, line):
    # """
    # Beamer Start
    # """
    # print("Beamer Start")
    #
    # def do_bc(self, line):
    #     """
    #     Beamer Stop
    #     """
    #     print("Beamer Stop")
    #
    # def do_bb(self, line):
    #     """
    #     Beamer Set brightness
    #     """
    #     print("Beamer Set briooghtness, ", line)
    #
    # def do_bcon(self, line):
    #     """
    #     Beamer Set Contrast
    #     """
    #     print("Beamer Set Contrast ", line)

    """
        Mediabox
    """

    # def do_di(self, line):
    #     """
    #     Mediabox set IP
    #     """
    #     print("Mediabox set IP ", line)
    #
    # def do_dn(self, line):
    #     """
    #     Mediabox set network name
    #     """
    #     print("Mediabox set network name ", line)
    #
    # def do_dp(self, line):
    #     """
    #     Mediabox set new w-lan password
    #     """
    #     print("Mediabox set new w-lan password ", line)
    #
    # def do_r(self, line):
    #     """
    #     Mediabox restart
    #     """
    #     print("Mediabox restart")
    #
    # def do_h(self, line):
    #     """
    #     Help
    #     """
    #     print("Use help instaed")
    #
    # def do_v(self, line):
    #     """
    #     Show Version
    #     """
    #     print("Show Version ")
    #
    # def do_s(self, line):
    #     """
    #     Show Status
    #     """
    #     print("Show Status ")
    #
    # def do_mvu(self, line):
    #     """
    #     Volume Up
    #     """
    #     print("Volume Up ")
    #
    # def do_mvd(self, line):
    #     """
    #     Volume Down
    #     """
    #     print("Volume Down ")
    #
    # def do_mvs(self, line):
    #     """
    #     Volume Set at?
    #     """
    #     print("Volume Set at? ", line)
    #
    # def do_mvm(self, line):
    #     """
    #     Volume Mute
    #     """
    #     print("Volume Mute ")

    """
        Others
    """

    def do_ls(self, line):
        """
        Lists the files of the upload directory
        """
        for filename in os.listdir(get_upload_folder()):
            if allowed_file(filename):
                print(filename,
                      get_human_size(os.path.getsize(os.path.join(get_upload_folder(), filename))),
                      datetime.datetime.fromtimestamp(
                          os.path.getmtime(os.path.join(get_upload_folder(), filename))
                      ).strftime("%Y-%m-%d %H:%M:%S"))

    def do_exit(self, line):
        """
        Exit the CLI
        """
        self.pres.stop()
        return True

    def do_EOF(self, line):
        self.pres.stop()
        return True


if __name__ == '__main__':
    BeamCli().cmdloop()