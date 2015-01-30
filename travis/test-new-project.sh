#!/bin/bash -ex

STATUS_CODE=$(curl --write-out %{http_code} --silent --output /dev/null "http://localhost/test/$1")

if [ $STATUS_CODE -eq 200 ]
then
    echo "OK"
    exit
else
    echo "Bad status code $STATUS_CODE"

    cd /tmp/testgeomapfish

    sudo cat /var/log/apache2/error.log
    sudo cat /var/log/apache2/access.log
    curl "http://localhost/test/$1"

    exit 1
fi
