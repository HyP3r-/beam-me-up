#!/usr/bin/env bash
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

# check user
if [[ $USER != "beam" ]]; then
    echo "This script must be run as beam!"
    exit 1
fi

# set enviroment
export DISPLAY=:0 || exit 1
export PYTHONPATH=$PYTHONPATH:/usr/local/lib/beam || exit 1

# run the programm
cd /usr/local/lib/beam/beam_cli
/usr/bin/env python beam_cli.py