#!/bin/bash -ex

RESULT=$(make $* 2>&1 | tail -n +2)

if [ "${RESULT}" != "" ]
then
    echo A Rule is running again
    make $*
    exit 1
fi
