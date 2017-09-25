#!/bin/bash

set -e

if [[ -z "$DB_CONNECTION" ]]
then
  echo "Using default DB connection"
else
  echo "Replacing DB connection from env"
  sed -i -e 's/${mapserver_connection}\([\" ]\)/'"$DB_CONNECTION"'\1/' `find /etc/mapserver -name *.map`
fi
