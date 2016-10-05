#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2013-2016, Camptocamp SA
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

here = os.path.abspath(os.path.dirname(__file__))
with open("README.rst") as f:
    text = f.read().split("\n")
    text = text[3:]
    text += ""
    text += "`Sources <https://github.com/camptocamp/c2cgeoportal/>`_"
    README = "\n".join(text)

install_requires = [
    "pyramid_multiauth",
    "pyramid_mako",  # to render the HTML files
    "psycopg2",
    "GeoAlchemy2",
    "SQLAHelper",
    "pyramid_tm",
    "papyrus",
    "ipcalc",
    "httplib2",
    # Needed by the developement.ini
    "pyramid_debugtoolbar",
    "OWSLib>=0.6.0",
    "dogpile.cache>=0.6",
    "Paste",
    "PasteDeploy",
    "PasteScript",
    # Needed by the production.ini
    "waitress",
    # WMST support
    "isodate",
    "pyramid_closure",
    "lingua",
    "PyYAML",
    "c2c.template>=1.3.0.dev",
]
install_requires += [
    requirement for requirement in
    open(os.path.join(here, "fixversions.txt")).read().splitlines()
    if len(requirement) > 0 and requirement[0] != "#"
]

setup_requires = [
]

tests_require = install_requires + [
]

setup(
    name="c2cgeoportal",
    version="2.1",
    description="c2cgeoportal",
    long_description=README,
    classifiers=[
        "Programming Language :: Python",
        "Framework :: Pylons",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
    ],
    author="Camptocamp",
    author_email="info@camptocamp.com",
    url="http://www.camptocamp.com/geospatial-solutions",
    keywords="web gis geoportail c2cgeoportal geocommune pyramid",
    packages=find_packages(exclude=["*.tests", "*.tests.*"]),
    include_package_data=True,
    zip_safe=False,
    install_requires=install_requires,
    setup_requires=setup_requires,
    tests_require=tests_require,
    test_suite="c2cgeoportal",
    entry_points={
        "console_scripts": [
            "print_tpl = c2cgeoportal.scripts.print_tpl:main",
            "manage_users = c2cgeoportal.scripts.manage_users:main",
            "c2ctool = c2cgeoportal.scripts.c2ctool:main",
            "db2pot = c2cgeoportal.scripts.db2pot:main",
            "themev1tov2 = c2cgeoportal.scripts.themev1tov2:main",
            "theme2fts = c2cgeoportal.scripts.theme2fts:main",
            "l10nv1tov2 = c2cgeoportal.scripts.l10nv1tov2:main",
            "import-ngeo-apps = c2cgeoportal.scripts.import_ngeo_apps:main",
            "gen-version = c2cgeoportal.scripts.gen_version:main",
            "ngeo-version = c2cgeoportal.scripts.import_ngeo_apps:ngeo_git_version",
            "create-demo-theme = c2cgeoportal.scripts.create_demo_theme:main",
        ],
        "pyramid.scaffold": [
            "c2cgeoportal_create = c2cgeoportal.scaffolds:TemplateCreate",
            "c2cgeoportal_update = c2cgeoportal.scaffolds:TemplateUpdate",
        ],
        "fanstatic.libraries": [
            "admin = c2cgeoportal.forms:fanstatic_lib",
        ],
        "lingua.extractors": [
            "geomapfish-theme = c2cgeoportal.lib.lingua_extractor:GeoMapfishThemeExtractor",
            "geomapfish-config = c2cgeoportal.lib.lingua_extractor:GeoMapfishConfigExtractor",
            "geomapfish-angular = c2cgeoportal.lib.lingua_extractor:GeoMapfishAngularExtractor",
        ],
    }
)
