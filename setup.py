import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = "c2cgeoportal, generic GIS portal made by Camptocamp"

install_requires = [
    'pyramid<=1.3.99,>=1.3.2',
    'WebError',
    'psycopg2',
    # sqlalchemy-migrate 0.7.2 and GeoAlchemy 0.7.1
    # don't work with SQLAlchemy 0.8.
    'sqlalchemy<=0.7.9',
    'sqlalchemy-migrate<=0.7.99',
    'sqlahelper',
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
    'tileforge>=0.2',
    'JSTools>=0.6',
    'simplejson',
    'PyYAML',
    'dogpile.cache',
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
    'nose==1.1.2',
    'nosexcover==1.0.7',
    'nose-progressive==1.3',
    'ipdbplugin==1.2',
    ]

tests_require = install_requires + [
    'mock==1.0.1',
    'testegg==1.0',
    ]

setup(name='c2cgeoportal',
      version='1.3.2',
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
          ('**.py', 'python', None),
          ('templates/**', 'mako', {'input_encoding': 'utf-8'})]},
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
