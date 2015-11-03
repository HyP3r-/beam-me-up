#######################################################################
#
#  This file is part of the 'Beam' project.
# 
#  (C) 2015 Gundolf Kiefer <gundolf.kiefer@hs-augsburg.de>
#      Hochschule Augsburg, University of Applied Sciences
#
#  Description:
#    This Makefile is to assist the building of a portable version
#    of the 'liblinphone' library <www.linphone.org>.
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





##### Configuration options #####

# Installation prefix (for binary and development files) ...
#PREFIX=/opt/linphone
PREFIX=/usr/local

# Common make options...
MAKE_OPT=-j 2     # use 2 parallel threads when building

# Select versions of the involved libraries...
#   The following versions are suitable for 'phone2l', 2015-06-10.
VER_BELLESIP=1.4.1
VER_LINPHONE=3.8.1
VER_ORTP=0.24.1
VER_MEDIASTREAMER=2.11.1



##### Common main targets #####

all: build

configure: configure-bellesip configure-linphone

build: .bellesip-built .linphone-built

install: install-bellesip install-linphone

uninstall: uninstall-bellesip uninstall-linphone
	for DIR in include/mediastreamer2 include/ortp include/linphone \
	  lib/mediastreamer/plugins lib/mediastreamer \
	  share/tutorials/linphone share/tutorials \
	  share/pixmaps/linphone \
	  share/sounds/linphone/rings share/sounds/linphone share/sounds \
	  share/gnome/help/linphone share/gnome/help share/gnome \
	  share/linphone; do \
	    rmdir ${PREFIX}/$$DIR; \
	  done

clean:
	rm -fr .bellesip-built
	make clean-bellesip
	rm -f .linphone-built
	make clean-linphone



##### Sub-targets for 'belle-sip' ... #####

.bellesip-configured:
	make configure-bellesip

.bellesip-built: .bellesip-configured
	make build-bellesip

configure-bellesip: .autogen belle-sip linphone linphone/oRTP linphone/mediastreamer2
	@echo "#############################################################"
	@echo "# Configuring belle-sip ...                                 #"
	@echo "#############################################################"
	@echo " "
	rm -f .bellesip-configured
	cd belle-sip; \
	  ./configure --prefix=${PREFIX} --disable-shared --enable-static --disable-tests
	touch .bellesip-configured
	@echo " "

build-bellesip: .autogen .bellesip-configured
	@echo "#############################################################"
	@echo "# Building belle-sip ...                                    #"
	@echo "#############################################################"
	@echo
	make ${MAKE_OPT} -w -C belle-sip 
	@echo
	make ${MAKE_OPT} -w -C belle-sip install DESTDIR=${PWD}/.bellesip-built
#	touch .bellesip-built
	@echo

install-bellesip: .bellesip-configured
	@echo "#############################################################"
	@echo "# Installing belle-sip ...                                  #"
	@echo "#############################################################"
	@echo
	make ${MAKE_OPT} -w -C belle-sip install
	@echo
  
uninstall-bellesip: .bellesip-configured
	@echo "#############################################################"
	@echo "# Installing belle-sip ...                                  #"
	@echo "#############################################################"
	@echo
	make ${MAKE_OPT} -w -C belle-sip uninstall
	@echo

clean-bellesip:
	make ${MAKE_OPT} -w -C belle-sip clean



##### Sub-targets for 'linphone' and sub-projects ... #####

.linphone-configured:
	make configure-linphone

.linphone-built: .linphone-configured
	make build-linphone

configure-linphone: linphone linphone/oRTP linphone/mediastreamer2 .bellesip-built
	@echo "#############################################################"
	@echo "# Configuring linphone with oRTP and mediastreamer2...      #"
	@echo "#############################################################"
	@echo
	rm -f .linphone-configured
	cd linphone; \
#	  PKG_CONFIG_PATH=${PWD}/.bellesip-built/${PREFIX}/lib/pkgconfig \
	  BELLESIP_CFLAGS=-I${PWD}/.bellesip-built/${PREFIX}/include \
	  BELLESIP_LIBS="-L${PWD}/.bellesip-built/${PREFIX}/lib -lbellesip -lantlr3c  -lpolarssl" \
	  LDFLAGS="-lm -lXext" \
	  ./configure --prefix=${PREFIX} --disable-shared --enable-static --disable-strict \
	  --disable-nls --disable-oss --disable-pulseaudio --disable-gsm --disable-matroska --disable-spandsp --disable-upnp --disable-opus \
	  --enable-x11 --disable-xv --disable-glx --disable-sdl --disable-theora --enable-vp8 --disable-g729bCN --with-srtp=none --disable-zlib --disable-notify \
	  --enable-date --enable-alsa --disable-lime --disable-msg-storage
	touch .linphone-configured
	@echo ""

#	  BELLESIP_CFLAGS=-I${PWD}/../belle-sip/include \
#	  BELLESIP_LIBS=-L${PWD}/../belle-sip/src \

build-linphone: .autogen .linphone-configured .bellesip-built
	@echo "#############################################################"
	@echo "# Building linphone ...                                     #"
	@echo "#############################################################"
	@echo
	test -f linphone/coreapi/liblinphone_gitversion.h \
	  || echo "#define LIBLINPHONE_GIT_VERSION \""${VER_LINPHONE}"\"" > linphone/coreapi/liblinphone_gitversion.h
	@echo
	make ${MAKE_OPT} -w -C linphone
	touch .linphone-built
	@echo

install-linphone: .linphone-configured .bellesip-built
	@echo "#############################################################"
	@echo "# Installing linphone ...                                   #"
	@echo "#############################################################"
	@echo
	make ${MAKE_OPT} -w -C linphone install
	@echo

uninstall-linphone: .linphone-configured
	@echo "#############################################################"
	@echo "# Installing linphone ...                                   #"
	@echo "#############################################################"
	@echo
	make ${MAKE_OPT} -w -C linphone uninstall
	@echo

clean-linphone:
	make ${MAKE_OPT} -w -C linphone clean



##### Helpers for source code downloading and packaging #####

.autogen:
	cd belle-sip; ./autogen.sh
	@echo
	cd linphone; ./autogen.sh
	@echo
	touch .autogen



### Working with git...

# Git-clone from original repo at linphone.org ...
clone:
	git clone git://git.linphone.org/belle-sip.git
	git clone git://git.linphone.org/linphone.git --recursive

# Remove cloned source trees ...
clone-clean:
	rm -fr belle-sip linphone

# Git-checkout selected versions ...
checkout:
	cd belle-sip; git checkout ${VER_BELLESIP}; echo
	cd linphone/mediastreamer2; git checkout ${VER_MEDIASTREAMER}; echo
	cd linphone/oRTP; git checkout ${VER_ORTP}; echo
	cd linphone; git checkout ${VER_LINPHONE}; echo


# Make tarballs from existing git-cloned source directories...
pack:
	DIR=belle-sip/; ( cd $$DIR; git archive --prefix=$$DIR ${VER_BELLESIP} -o ../bellesip-${VER_BELLESIP}.tar.gz )
	DIR=linphone/; ( cd $$DIR; git archive --prefix=$$DIR ${VER_LINPHONE} -o ../linphone-${VER_LINPHONE}.tar.gz )
	DIR=linphone/oRTP/; ( cd $$DIR; git archive --prefix=$$DIR ${VER_ORTP} -o ../../ortp-${VER_ORTP}.tar.gz )
	DIR=linphone/mediastreamer2/; ( cd $$DIR; git archive --prefix=$$DIR ${VER_MEDIASTREAMER} -o ../../mediastreamer-${VER_MEDIASTREAMER}.tar.gz )



### Working without git...

# Unpack tarballs to source directories ...
unpack:
	tar zxf bellesip-${VER_BELLESIP}.tar.gz
	tar zxf linphone-${VER_LINPHONE}.tar.gz
	tar zxf ortp-${VER_ORTP}.tar.gz
	tar zxf mediastreamer-${VER_MEDIASTREAMER}.tar.gz

# Remove source directories ...
# (Warning: this also removes eventually cloned source trees!)
unpack-clean:
	rm -fr belle-sip linphone
