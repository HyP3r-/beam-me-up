# Beam me up!

This Software provides a small presentation system.

## Plattform

This system was designed for debian jessie on cubietruck.

## Librarys

Fist of all you have to install some software an librarys. Bevore you start,
you should update your system:

    # apt-get update
    # apt-get upgrade

Default software:

    # apt-get install dnsmasq hostapd ntp ntpdate build-essential

Software for beam_wm:

    # apt-get install nodm x11proto-core-dev libx11-dev libxrandr-dev \
                      xloadimage xinit xserver-xorg 

Software for beam_vnc:

    # apt-get install xutils-dev openjdk-7-jre openjdk-7-jdk libxt-dev \
                      libxmu-headers libxaw7-dev libjpeg62-turbo-dev

Software for beam_web:

    # apt-get install python-xlib python-pip python-xlib libpython2.7-dev
    # pip install --upgrade flask flask-login flask-wtf

Software for beam_application:

    # apt-get install evince vlc
    # pip install --upgrade pypdf2 PyUserInput 

## Config Files

After the installation of the librarys you should insert the config files in
the system. You can find all config files in the config folder.

Copy all files from /configs/etc to /etc. Please make sure that you made
following files runnable:
   
- /etc/network/if-up.d/beam
- /etc/cron.hourly/beam_clean_up.sh
- /etc/init.d/{correctdate,hostapd,nodm}

Please consider that you are overwriting files such as hostname, hosts and 
interfaces. Your system gets a new hostname, other network interface 
addresses and new issue file.

Deamons such as hostapd and nodm were installed through dpkg, but correctdate
(a small workaround for clock problem on cubietruck) is new. You have to 
install this deamon:

    # update-rc.d correctdate defaults

## User

After that you have to create a new user called "beam".

    # adduser admin

Now you should be able to copy the /configs/home folder to /home. Please make
sure that you have made following files runnable:

/home/beam/.xsession

nodm can now initialize the x-server and run this script.

## Local Librarys

This project brings two librarys which now should be installed. Go into the
folder external and follow the README files.

## Compiliation

After you have installed those tow librarys you can now compile all project
components:

    # make

## Installation

Now, all project components were compilied and build you can install the system:

    # make install

## Startup

After that all you can restart the services networking, hostapd and nodm:

    # service networking restart
    # service hostapd restart
    # service nodm restart

nodm will now execute the .xession script, this will start the website and the
window manager. You can start if you connect to http://192.168.42.1/.
    