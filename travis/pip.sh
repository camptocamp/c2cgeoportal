#!/bin/bash

# Used to return the result code given by pip instance of by grep
ARGS="--log /tmp/pip.log"
PIP_VERSION=`.build/venv/bin/pip --version|awk '{print $2}' | awk -F. '{print $1}'`
if [ ${PIP_VERSION} -ge 6 ]
then
    ARGS="${ARGS} --cache-dir /tmp/pip-cache"
fi
.build/venv/bin/pip ${ARGS} $* | grep '^Collecting '
if [ ${PIPESTATUS[0]} -ne 0 ]
then
    cat /tmp/pip.log
    exit 1
fi
exit 0
