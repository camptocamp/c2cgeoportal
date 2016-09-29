#!/bin/bash -x

cd $1
shift

make $* > /dev/null 2> make-err

RESULT=$(cat make-err)

rm make-err --force

if [ "${RESULT}" != "" ] \
    && [ "${RESULT}" != "AH00558: apache2: Could not reliably determine the server's fully qualified domain name, using 127.0.1.1. Set the 'ServerName' directive globally to suppress this message" ]
then
    echo There is some error output in the make
    make $* > /dev/null
    cd - > /dev/null
    exit 1
fi
cd - > /dev/null
