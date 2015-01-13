#!/bin/bash

status=`git status -s`

if [ "$status" != "" ];
then
    echo Build generates changes
    git status
    git diff
    exit 1
fi
