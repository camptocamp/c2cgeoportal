#!/usr/bin/env python3

import time
import sys
import re
import os
import subprocess

os.environ["DEBUG"] = "TRUE"
p = subprocess.Popen(["make"] + sys.argv[1:], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
while p.returncode == None:
    time.sleep(0.2)
    p.poll()

lines = p.stderr.read().decode("utf-8").split("\n")
lines = [l for l in lines if l != ""]
lines = [l for l in lines if "make: Nothing to be done for " not in l]
lines = [l for l in lines if " warning: overriding recipe for target " not in l]
lines = [l for l in lines if " warning: ignoring old recipe for target " not in l]

if p.returncode > 0 or len(lines) > 0:
    print("A Rule is running again, code: {}\n\n{}\n\n{}\n---".format(
        p.returncode, "\n".join(lines), p.stdout.read().decode("utf-8")
    ))
    subprocess.call(["make"] + sys.argv[1:])
    exit(2)
