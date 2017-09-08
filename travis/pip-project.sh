#!/bin/bash

ARGS="--log /tmp/pip.log"

.build/venv/bin/pip ${ARGS} $* | grep '^\(Collecting\|  Downloading\) '

if [ ${PIPESTATUS[0]} -eq 0 ]
then
    exit 0
fi

for N in {1..3}
do
    echo RETRY...
    .build/venv/bin/pip ${ARGS} $* | grep '^\(Collecting\|  Downloading\) '

    if [ ${PIPESTATUS[0]} -eq 0 ]
    then
        exit 0
    fi
done
cat /tmp/pip.log
exit 1
