#######################################################################
#
#  This file is part of the 'Beam' project.
# 
#  (C) 2015 Andreas Fendt, Martin Demharter and Yordan Pavlov
#      Hochschule Augsburg, University of Applied Sciences
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#    
#######################################################################

BUILD_DIR = build
PREFIX = /usr/local

all: preparation beam-application beam-cli beam-projector beam-vnc beam-web beam-wm

### Copy und Compiliation ###

preparation:
	mkdir -p $(BUILD_DIR)


beam-application:
	cp -rf beam_application $(BUILD_DIR)


beam-cli:
	cp -rf beam_cli $(BUILD_DIR)
	chmod +x $(BUILD_DIR)/beam_cli/beam_cli.sh
	chmod +x $(BUILD_DIR)/beam_cli/beam_cli.py

beam-projector:
	cp -rf beam_projector $(BUILD_DIR)

beam-vnc:
	$(MAKE) -C beam_vnc config
	$(MAKE) -C beam_vnc all

beam-web:
	cp -rf beam_web/* $(BUILD_DIR)
	chmod +x $(BUILD_DIR)/run.py

beam-wm:
	$(MAKE) -C beam_wm all

### INSTALL ###
	
install: install-build install-wm install-vnc install-cli

install-build:
	mkdir -p $(PREFIX)/lib/beam
	cp -rf $(BUILD_DIR)/* $(PREFIX)/lib/beam 
	ln -s $(PREFIX)/lib/beam/run.py $(PREFIX)/bin/beam_web	

install-wm:
	cp -f beam_wm/bin/smallwm $(PREFIX)/bin/beam_wm
	
install-vnc:
	cp -f beam_vnc/vnc_unixsrc/vncviewer/vncviewer $(PREFIX)/bin/beam_vnc 

install-cli:
	ln -s $(PREFIX)/lib/beam/beam_cli/beam_cli.sh $(PREFIX)/bin/beam_cli
	
install-rights:
	chown -R root:staff $(PREFIX)/lib/beam \
			$(PREFIX)/bin/beam_wm \
			$(PREFIX)/bin/beam_web \
			$(PREFIX)/bin/beam_vnc 
	chown -R beam:beam $(PREFIX)/lib/beam/beam_web/static/upload
	chown -R beam:beam $(PREFIX)/lib/beam/beam_web/static/download 
	
### CLEAN ###
	
clean:
	$(MAKE) -C beam_vnc clean
	$(MAKE) -C beam_wm clean
	rm -rf $(BUILD_DIR)