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

here = os.path.abspath(os.path.dirname(__file__))
README = """c2cgeoportal is the server part of `GeoMapFish <http://geomapfish.org/>`_,
the client part is `ngeo <https://github.com/camptocamp/ngeo/>`_,
the old client and API part is `CGXP <https://github.com/camptocamp/cgxp/>`_.

Read the `Documentation <https://camptocamp.github.io/c2cgeoportal/master/>`_.

`Sources <https://github.com/camptocamp/c2cgeoportal/>`_"""

TRAVIS_TAG = os.environ.get('GIT_TAG')
MAJOR_VERSION = os.environ.get('MAJOR_VERSION')
VERSION = TRAVIS_TAG if TRAVIS_TAG is not None and TRAVIS_TAG != '' else \
    MAJOR_VERSION if MAJOR_VERSION is not None and MAJOR_VERSION != '' else 'dev'

install_requires = [
    'c2cgeoportal-commons==' + VERSION,
    'c2cwsgiutils',
    'c2c.template>=1.4.0',  # Makefile
    'dateutils',
    'defusedxml',
    'dogpile.cache>=0.6',
    'GeoAlchemy2',
    'httplib2',
    'ipcalc',
    'isodate',  # WMST support
    'lingua',
    'OWSLib>=0.6.0',
    'papyrus',
    'Paste',
    'PasteDeploy',
    'PasteScript',
    'psycopg2-binary',
    'pycrypto',
    'pyramid<=1.9.99',
    'pyramid_closure',
    'pyramid_debugtoolbar',  # Needed by the development.ini
    'pyramid_mako',  # to render the HTML files
    'pyramid_multiauth',
    'pyramid_tm',
    'PyYAML',
    'SQLAlchemy',
    'Fiona',
    'redis',
    'rasterio',
]

setup_requires = [
]

tests_require = install_requires + [
]

setup(
    name='c2cgeoportal-geoportal',
    version=VERSION,
    description='c2cgeoportal',
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
    include_package_data=True,
    zip_safe=False,
    install_requires=install_requires,
    setup_requires=setup_requires,
    tests_require=tests_require,
    entry_points={
        'console_scripts': [
            'manage_users = c2cgeoportal_geoportal.scripts.manage_users:main',
            'c2cupgrade = c2cgeoportal_geoportal.scripts.c2cupgrade:main',
            'db2pot = c2cgeoportal_geoportal.scripts.db2pot:main',
            'themev1tov2 = c2cgeoportal_geoportal.scripts.themev1tov2:main',
            'theme2fts = c2cgeoportal_geoportal.scripts.theme2fts:main',
            'l10nv1tov2 = c2cgeoportal_geoportal.scripts.l10nv1tov2:main',
            'import-ngeo-apps = c2cgeoportal_geoportal.scripts.import_ngeo_apps:main',
            'npm-packages = c2cgeoportal_geoportal.scripts.npm_packages:main',
            'ngeo-version = c2cgeoportal_geoportal.scripts.npm_packages:ngeo_git_version',
            'create-demo-theme = c2cgeoportal_geoportal.scripts.create_demo_theme:main',
            'treeitem-uniquename = c2cgeoportal_geoportal.scripts.treeitem_uniquename:main',
            'urllogin = c2cgeoportal_geoportal.scripts.urllogin:main',
        ],
        'pyramid.scaffold': [
            'c2cgeoportal_create = c2cgeoportal_geoportal.scaffolds:TemplateCreate',
            'c2cgeoportal_update = c2cgeoportal_geoportal.scaffolds:TemplateUpdate',
            'c2cgeoportal_nondockercreate = c2cgeoportal_geoportal.scaffolds:TemplateNondockerCreate',
            'c2cgeoportal_nondockerupdate = c2cgeoportal_geoportal.scaffolds:TemplateNondockerUpdate',
        ],
        'lingua.extractors': [
            'geomapfish-theme = c2cgeoportal_geoportal.lib.lingua_extractor:GeoMapfishThemeExtractor',
            'geomapfish-config = c2cgeoportal_geoportal.lib.lingua_extractor:GeoMapfishConfigExtractor',
            'geomapfish-angular = c2cgeoportal_geoportal.lib.lingua_extractor:GeoMapfishAngularExtractor',
        ],
    }
)
