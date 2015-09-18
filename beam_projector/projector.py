# -*- coding: utf-8; -*-
# Beam Projector
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
import ConfigParser
import os


class Projector(object):
    def __init__(self):
        # Read config
        config = ConfigParser.ConfigParser()
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "../../../etc/beam-projector.cfg")
        config.read(path)
        self.current_projector_manufacturer = config.get("projector", "current_projector_manufacturer")
        self.current_projector_model = config.get("projector", "current_projector_model")
        # Load Library
        try:
            self.projector = __import__("beam_projector.{0}.{1}".format(self.current_projector_manufacturer,
                                                                        self.current_projector_model),
                                        globals(),
                                        locals(),
                                        [""])
        except Exception, e:
            pass

    def __getattr__(self, name):
        def method(*args):
            try:
                return getattr(self.projector, name)()
            except Exception, e:
                return e.message

        return method

# test this system
if __name__ == "__main__":
    projector = Projector()
    projector.mute_on()