#!/bin/sh -ex

cd ${deploy["code_destination"]}
./docker-run make --makefile=$TARGET.mk build -j2
FINALISE=TRUE make --makefile=$TARGET.mk build -j2
