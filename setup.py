# Copyright (c) 2013, Camptocamp SA
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
README = """c2cgeoportal is the server part of `GeoMapFish <http://geomapfish.org/>`_,
the client part is `CGXP <https://github.com/camptocamp/cgxp/>`_.

`Documentation <http://docs.camptocamp.net/c2cgeoportal/>`_

`Announcement <https://www.camptocamp.com/en/actualite/geomapfish-release-of/>`_

`Sources <https://github.com/camptocamp/c2cgeoportal/>`_"""

install_requires = [
    'pyramid<=1.5.99,>=1.5.0',
    'pyramid_multiauth',
    'pyramid_mako',
    'pyramid_chameleon',
    'WebError',
    'psycopg2',
    # sqlalchemy-migrate 0.7.2 and GeoAlchemy 0.7.1
    # don't work with SQLAlchemy 0.8.
    'SQLAlchemy<=0.7.9',
    'sqlalchemy-migrate<=0.7.99',
    'SQLAHelper',
    'pyramid_tm',
    'papyrus>=0.10dev1',
    'papyrus_ogcproxy>=0.2dev1',
    'httplib2',
    'Babel',
    'pyramid_formalchemy>=0.4.3',
    'fa.jquery>=0.9.5',
    # fa.jquery uses js.jqueryui_selectmenu, whose released
    # version (0.1) doesn't work with js.jquery > 1.7.1.
    'js.jquery==1.7.1',
    # The latest js.jqgrid lib (4.4.1) needs a DOCTYPE for IE8
    # See: https://github.com/camptocamp/c2cgeoportal/issues/411
    'js.jqgrid==4.3.1-1',
    'fanstatic>=0.11.3',
    'GeoFormAlchemy>=0.4',
    'GeoAlchemy>=0.7,<=0.7.99',
    # With Formalchemy 1.4.3 the Layer types 'WMTS' and 'no 2D' are not visible.
    'FormAlchemy<=1.4.2',
    'OWSLib>=0.6.0',
    'tilecloud-chain>=0.2',
    'JSTools>=0.6',
    'simplejson',
    'PyYAML',
    'dogpile.cache',
    'PasteScript',
    # Used in the CONST_buildout.cfg
    # Needs to be here to correctly generate version.cfg
    'c2c.recipe.cssmin',
    'c2c.recipe.facts',
    'c2c.recipe.jarfile',
    'c2c.recipe.msgfmt',
    'collective.recipe.cmd',
    'collective.recipe.modwsgi',
    'JSTools',
    'z3c.recipe.filetemplate',
    # Needed by the production.ini
    'waitress',
    # WMST support
    'isodate',
    'nose==1.3.0',
]

# nose plugins with options set in setup.cfg cannot be in
# tests_require, they need be in setup_requires
#
# nose has version fixed because we have regression with
# command line options.
# This also forces us to stick with nose-progressive 1.3.
# See https://github.com/camptocamp/c2cgeoportal/pull/333
#
# Others are fixed because the versions are mot listed
# by buildout.dumppickedversions.
setup_requires = [
    'nosexcover==1.0.8',
]

tests_require = install_requires + [
    'testegg==1.0',
]

setup(
    name='c2cgeoportal',
    version='1.5.5',
    description='c2cgeoportal',
    long_description=README,
    classifiers=[
        "Programming Language :: Python",
        "Framework :: Pylons",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
    ],
    author='camptocamp',
    author_email='info@camptocamp.com',
    url='http://www.camptocamp.com/geospatial-solutions',
    keywords='web gis geoportail c2cgeoportal geocommune pyramid',
    packages=find_packages(),
    include_package_data=True,
    message_extractors={'c2cgeoportal': [
        ('static/**', 'ignore', None),
        ('tests/**', 'ignore', None),
        ('scaffolds/create/+package+/templates/**', 'mako', {'input_encoding': 'utf-8'}),
        ('scaffolds/**', 'ignore', None),
        ('**.py', 'python', None),
        ('templates/**', 'mako', {'input_encoding': 'utf-8'}),
    ]},
    zip_safe=False,
    install_requires=install_requires,
    setup_requires=setup_requires,
    tests_require=tests_require,
    test_suite="c2cgeoportal",
    entry_points={
        'console_scripts': [
            'print_tpl = c2cgeoportal.scripts.print_tpl:main',
            'manage_users = c2cgeoportal.scripts.manage_users:main',
            'manage_db = c2cgeoportal.scripts.manage_db:main',
            'c2ctool = c2cgeoportal.scripts.c2ctool:main',
        ],
        'pyramid.scaffold': [
            'c2cgeoportal_create = c2cgeoportal.scaffolds:TemplateCreate',
            'c2cgeoportal_update = c2cgeoportal.scaffolds:TemplateUpdate',
        ],
        'fanstatic.libraries': [
            'admin = c2cgeoportal.forms:fanstatic_lib',
        ],
    }
)
