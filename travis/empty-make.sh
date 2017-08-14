#!/bin/bash -ex

RESULT=$(DEBUG=TRUE make $* 2>&1)

if [ "${RESULT}" != "make: Nothing to be done for 'build'." ] && \
   [ "${RESULT}" != "" ]
then
    echo A Rule is running again
    DEBUG=TRUE make $*
    exit 2
fi
