#!/usr/bin/env bash
# Script to start the web server and window manager
# Copyright (C) 2015 Andreas Fendt, Martin Demharter and
# Yordan Pavlov - All Rights Reserved
# Permission to copy and modify is granted under the GNU General Public License
# Last revised 06/15/2015

# start web server
webserver=/usr/local/bin/beam_web
webserver_pid=~/beam_web.pid
if [ -x $webserver ]; then
    if [ -e $webserver_pid ];
    then
        pkill -TERM -P $(cat $webserver_pid) &>/dev/null
    fi
    sleep 1
    $webserver &>/dev/null &
    echo $! > $webserver_pid
fi

# Set background to your favorite pic and turn the screen safer off
xsetbg -fullscreen /home/beam/wallpaper.png  &>/dev/null &
xset -dpms s off &>/dev/null

# just start the window manager
/usr/local/bin/beam_wm

# kill webserver
if [ -e $webserver_pid ];
then
    pkill -TERM -P $(cat $webserver_pid) &>/dev/null
fi
