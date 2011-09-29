#!/bin/bash

#
# This script can be used to automate the building of the project's
# JavaScript code during the development phase.
#
# It requires the nosier Python package, which can installed in the
# buildout Python env.
#
# If the libnotify-bin Debian package is installed, the script will
# display nice popup messages.
#
# To use it enter the following command at the root of the project
# (where the jsbuild dir is):
#
# $ nosier -p c2cgeoportal/static -b 'build' -b '*.sw*' jsbuild/continuous_build.sh

state_file="/tmp/.javascript_build_failed"

notify_send=$(which notify-send)

buildout/bin/buildout -c buildout_elemoine.cfg install jsbuild

if [[ $? -ne 0 ]]; then
    msg=
    if [[ -n $notify_send ]]; then
        $notify_send -i /usr/share/icons/gnome/32x32/actions/stop.png "JS build failed" "check your deps..."
    else
        echo "JS build failed, check your deps"
    fi
    touch ${state_file}
    exit 1
elif [[ -f ${state_file} ]]; then
    if [[ -n $notify_send ]]; then
        $notify_send "JS build fixed"
    else
        echo "JS build fixed"
    fi
    rm -f ${state_file}
fi

exit 0
