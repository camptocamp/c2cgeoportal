#!/bin/bash -ex

RESULT=$(make $* 2>&1)

if [ "${RESULT}" != "" ]
then
    echo A Rule is running again
    DEBUG=TRUE make $*
    exit 1
fi
