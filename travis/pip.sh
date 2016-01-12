#!/bin/bash

ARGS="--log /tmp/pip.log"
PIP_VERSION=`.build/venv/bin/pip --version|awk '{print $2}' | awk -F. '{print $1}'`

if [ ${PIP_VERSION} -ge 6 ]
then
    ARGS="${ARGS} --cache-dir /tmp/pip-cache"
fi

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
