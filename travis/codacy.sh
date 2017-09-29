#!/bin/bash -ex

export CODACY_PROJECT_TOKEN=1605f78ffb214af5ba6cb172a95db5d1
coverage xml
python-codacy-coverage -r coverage.xml
