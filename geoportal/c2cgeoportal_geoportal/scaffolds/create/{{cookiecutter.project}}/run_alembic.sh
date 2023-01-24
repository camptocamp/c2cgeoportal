#!/bin/bash -eu
# Upgrade the DB.
#
# Mostly useful in a Docker environment.

for ini in *alembic*.ini; do
    if [[ -f "$ini" ]]; then
        echo "$ini ==========================="
        alembic -c "$ini" upgrade head
    fi
done
