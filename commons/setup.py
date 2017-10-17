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

from setuptools import setup, find_packages

README = open('README.md').read()

setup(
    name="c2cgeoportal-commons",
    version="2.3.0.dev0",
    description="c2cgeoportal commons",
    long_description=README,
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
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
        "c2cgeoform",
        "papyrus",
        'lingua>=2.4',
        'babel',
        'deform',
        'pyproj',  # sudo apt install python3-dev", why not with c2cgeoform ?
        'ColanderAlchemy>=0.3.2'  # why not with c2cgeoform ?
    ],
    extras_require={
        'testing': [
            'psycopg2',
            'pytest',
            'pytest-cov',
            'flake8==3.4.1',
        ],
    },
    entry_points={
        'console_scripts': [
            'initialize_db_main = c2cgeoportal_commons.scripts.initializedb:main',
        ],
        'paste.app_factory': [
            'test_app = c2cgeoportal_commons.tests:app',
        ],
    },
)
