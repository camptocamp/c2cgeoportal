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

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS 'AS IS' AND
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

HERE = os.path.abspath(os.path.dirname(__file__))
README = """c2cgeoportal is the server part of `GeoMapFish <http://geomapfish.org/>`_,
the client part is `ngeo <https://github.com/camptocamp/ngeo/>`_.

Read the `Documentation <https://camptocamp.github.io/c2cgeoportal/master/>`_.

`Sources <https://github.com/camptocamp/c2cgeoportal/>`_"""
VERSION = os.environ.get('VERSION', 'dev')


with open(os.path.join(HERE, 'requirements.txt')) as f:
    install_requires = f.read().splitlines()

setup_requires = []

tests_require = []

setup(
    name='c2cgeoportal_geoportal',
    version=VERSION,
    description='c2cgeoportal geoportal',
    long_description=README,
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Framework :: Pyramid',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
    ],
    author='Camptocamp',
    author_email='info@camptocamp.com',
    url='http://www.camptocamp.com/solutions/geospatial/',
    keywords='web gis geoportail c2cgeoportal geocommune pyramid',
    packages=find_packages(exclude=['tests.*']),
    package_data={'c2cgeoportal_geoportal': ['py.typed']},
    include_package_data=True,
    zip_safe=False,
    install_requires=install_requires,
    setup_requires=setup_requires,
    tests_require=tests_require,
    entry_points={
        'console_scripts': [
            'manage-users = c2cgeoportal_geoportal.scripts.manage_users:main',
            'c2cupgrade = c2cgeoportal_geoportal.scripts.c2cupgrade:main',
            'theme2fts = c2cgeoportal_geoportal.scripts.theme2fts:main',
            'create-demo-theme = c2cgeoportal_geoportal.scripts.create_demo_theme:main',
            'urllogin = c2cgeoportal_geoportal.scripts.urllogin:main',
        ],
        'pyramid.scaffold': [
            'c2cgeoportal_create = c2cgeoportal_geoportal.scaffolds:TemplateCreate',
            'c2cgeoportal_update = c2cgeoportal_geoportal.scaffolds:TemplateUpdate',
        ],
        'lingua.extractors': [
            'geomapfish-theme = c2cgeoportal_geoportal.lib.lingua_extractor:GeomapfishThemeExtractor',
            'geomapfish-config = c2cgeoportal_geoportal.lib.lingua_extractor:GeomapfishConfigExtractor',
            'geomapfish-angular = c2cgeoportal_geoportal.lib.lingua_extractor:GeomapfishAngularExtractor',
        ],
        'plaster.loader_factory': [
            'c2cgeoportal=c2cgeoportal_geoportal.lib.loader:Loader',
            'c2cgeoportal+ini=c2cgeoportal_geoportal.lib.loader:Loader',
            'c2cgeoportal+egg=c2cgeoportal_geoportal.lib.loader:Loader',
        ],
        'plaster.wsgi_loader_factory': [
            'c2cgeoportal=c2cgeoportal_geoportal.lib.loader:Loader',
            'c2cgeoportal+ini=c2cgeoportal_geoportal.lib.loader:Loader',
            'c2cgeoportal+egg=c2cgeoportal_geoportal.lib.loader:Loader',
        ],
    }
)
