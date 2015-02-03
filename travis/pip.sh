#!/bin/bash

# Used to return the result code given by pip instead of grep
.build/venv/bin/pip --log /tmp/pip.log $* | grep '^Collecting '
if [ ${PIPESTATUS[0]} -ne 0 ]
then
    cat /tmp/pip.log
    exit 1
fi
exit 0
