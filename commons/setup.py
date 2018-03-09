#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2013-2017, Camptocamp SA
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
from setuptools import setup, find_packages

README = open('README.md').read()

TRAVIS_TAG = os.environ.get("GIT_TAG")
MAJOR_VERSION = os.environ.get("MAJOR_VERSION")
VERSION = TRAVIS_TAG if TRAVIS_TAG is not None and TRAVIS_TAG != "" else \
    MAJOR_VERSION if MAJOR_VERSION is not None and MAJOR_VERSION != "" else "dev"

setup(
    name="c2cgeoportal-commons",
    version=VERSION,
    description="c2cgeoportal commons",
    long_description=README,
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        "Framework :: Pyramid",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
    ],
    author="Camptocamp",
    author_email="info@camptocamp.com",
    url="http://www.camptocamp.com/solutions/geospatial/",
    packages=find_packages(exclude=["tests.*"]),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'babel',
        'ColanderAlchemy>=0.3.2',  # why not with c2cgeoform ?
        'deform',
        'lingua>=2.4',
        'papyrus',
        'pyproj',  # sudo apt install python3-dev", why not with c2cgeoform ?
    ],
    extras_require={
        'testing': [
            'psycopg2-binary',
            'pytest',
            'pytest-cov',
            'flake8',
            'PyYAML',
        ],
    },
)
