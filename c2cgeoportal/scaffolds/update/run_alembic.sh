#!/bin/bash
# Upgrade the DB.
#
# Mostly useful in a Docker environment.

set -e

for ini in *alembic*.ini
do
    if [[ -f $ini ]]
    then
        echo "$ini ==========================="
        alembic -c $ini upgrade head
    fi
done
