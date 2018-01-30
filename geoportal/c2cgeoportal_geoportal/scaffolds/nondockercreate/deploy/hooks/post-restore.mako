#!/bin/sh -ex

cd ${deploy["code_destination"]}
make --makefile=$TARGET.mk build -j2

#rm apache/maintenance.enable
rm /tmp/np
