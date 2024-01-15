#!/bin/bash -eu

sphinx-build -b html -d _build/doctrees . _build/html
echo Documentation Success
