#!/bin/bash

# This script will fail (return code = 1) if there is one
# modified or a new file.

if [ $# -gt 0 ]
then
    cd $1
fi

# Checkout po file to don't failed on them
git checkout */locale/*/LC_MESSAGES/*.po

status=`git status -s`

if [ "$status" != "" ]
then
    echo Build generates changes
    git status
    git diff
    exit 1
fi
