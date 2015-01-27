#!/bin/bash

if [ $# -gt 0 ]
then
    cd $1
fi

status=`git status -s`

if [ "$status" != "" ]
then
    echo Build generates changes
    git status
    git diff
    exit 1
fi
