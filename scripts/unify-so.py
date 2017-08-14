#!/usr/bin/python3

import sys
import re
import subprocess

files = subprocess.check_output(["find", sys.argv[1], "-name", "*.cpython-*.so"]).decode("utf-8").split()
re1 = re.compile("(.*)\.cpython-.*\.so")
re2 = re.compile(".*/([^/]*)\.so")

for file_ in files:
    subprocess.check_call(["ln", "-s", re2.sub(r"\1.so", file_), re1.sub(r"\1.so", file_)])
