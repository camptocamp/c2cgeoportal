import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = "c2cgeoportal, generic gis protail made by camptocamp"

install_requires = [
    'pyramid<=1.3.99,>=1.3.2',
    'WebError',
    'psycopg2',
    'sqlalchemy',
    'sqlalchemy-migrate',
    'sqlahelper',
    'pyramid_tm',
    'papyrus>=0.9',
    'papyrus_ogcproxy',
    'httplib2',
    'Babel',
    'pyramid_formalchemy>=0.4.2',
    'fa.jquery>=0.9.5',
    'fanstatic>=0.11.3',
    'GeoFormAlchemy>=0.4',
    'GeoAlchemy>=0.7',
    'OWSLib',
    'tileforge>=0.2',
    'JSTools>=0.6',
    ]

# nose plugins with options set in setup.cfg cannot be in
# tests_require, they need be in setup_requires
setup_requires = [
    'nose',
    'nosexcover',
    ]

tests_require = install_requires + [
    'mock',
    ]

setup(name='c2cgeoportal',
      version='0.7',
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
