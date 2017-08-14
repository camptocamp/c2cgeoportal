#!/bin/bash -ex

RESULT=$(make $* 2>&1)

if [ "${RESULT}" != "make: Nothing to be done for 'build'." ]
then
    echo A Rule is running again
    DEBUG=TRUE make $*
    exit 1
fi
