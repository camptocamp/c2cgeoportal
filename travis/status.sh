#!/bin/bash

# This script will fail (return code = 1) if there is one
# modified or a new file.

if [ $# -gt 0 ]
then
    cd $1
fi

status=`git status --short`

if [ "$status" != "" ]
then
    echo Build generates changes
    git status
    git diff
    exit 1
fi
