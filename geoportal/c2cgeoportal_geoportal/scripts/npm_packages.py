# -*- coding: utf-8 -*-

# Copyright (c) 2011-2018, Camptocamp SA
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# The views and conclusions contained in the software and documentation are those
# of the authors and should not be interpreted as representing official policies,
# either expressed or implied, of the FreeBSD Project.


import os
import re
import subprocess
from json import loads
from argparse import ArgumentParser


RE_NPM_VERSION = re.compile("^([0-9]+)\.([0-9]+)\.([0-9]+)$")
RE_NPM_PRERELEASE_VERSION = re.compile("^([0-9]+)\.([0-9]+)\.([0-9]+)\.?([a-z]+)([0-9]+)$")


def _ngeo_version():
    if "TRAVIS_TAG" in os.environ and os.environ["TRAVIS_TAG"] != "":
        match = RE_NPM_VERSION.match(os.environ["TRAVIS_TAG"])
        prerelease_match = RE_NPM_PRERELEASE_VERSION.match(os.environ["TRAVIS_TAG"])
        if match is not None:
            return "{}.{}.{}".format(match.group(1), match.group(2), match.group(3))
        if prerelease_match is not None:
            return "{}.{}.{}-{}.{}".format(
                prerelease_match.group(1),
                prerelease_match.group(2),
                prerelease_match.group(3),
                prerelease_match.group(4),
                prerelease_match.group(5)
            )
    return None


def _get_ngeo_version():
    version = _ngeo_version()
    if version is not None:
        return version
    return "https://api.github.com/repos/camptocamp/ngeo/tarball/{}".format(
        subprocess.check_output(["git", "rev-parse", "HEAD"], cwd="ngeo").decode("utf-8").strip()
    )


def ngeo_git_version():
    version = _ngeo_version()
    print(os.environ["VERSION"] if version is None else version)


def main():
    """
    Extract npm packages
    """

    parser = ArgumentParser(description='Extract npm packages')

    parser.add_argument('--ngeo', action="store_true", help="Add ngeo package")
    parser.add_argument('--src', action='append', metavar='SRC', help="The ngeo source file")
    parser.add_argument('--dst', metavar='DST', help="The destination file")
    parser.add_argument('excludes', nargs='*', metavar='EXCLUDE', help="The npm package to exclude")

    args = parser.parse_args()

    packages = {}
    for src_ in args.src:
        with open(src_) as src:
            input_data = loads(src.read())
            packages.update(input_data.get('devDependencies', {}))
            packages.update(input_data.get('dependencies', {}))
    if args.ngeo:
        # Freeze the ngeo version
        packages["ngeo"] = _get_ngeo_version()
    for package in args.excludes:
        if package in packages:
            del packages[package]

    data = " ".join(["{}@{}".format(p, v) for p, v in packages.items()])
    data = data + "\n"

    with open(args.dst, "wt") as dst:
        dst.write(data)
