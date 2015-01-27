#!/bin/bash -e


# TODO
# - Actually it's not working on Travis ...
# - Should test the checkers

STATUS_CODE=$(curl --write-out %{http_code} --silent --output /dev/null http://localhost/test/wsgi/viewer.js)

if [ $STATUS_CODE -eq 200 ]
then
    echo "OK"
    exit
else
    echo "Bad status code $STATUS_CODE"

    cd /tmp/test

    sudo cat /var/log/apache2/error.log
    curl http://localhost/test/wsgi/viewer.js

    exit 1
fi
