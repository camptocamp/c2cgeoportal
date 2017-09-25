#!/bin/bash

# This script will fail (return code = 1) if there is one
# modified or a new file.

status=$(git status --short)

if [ "$status" != "" ]
then
    echo Build generates changes
    git status
    git diff
    exit 2
fi
