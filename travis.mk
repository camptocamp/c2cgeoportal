VARS_FILE ?= vars_travis.yaml
VARS_FILES += vars_travis.yaml
PIP_CMD = travis/pip.sh
VIRTUALENV_CMD = virtualenv

include Makefile
