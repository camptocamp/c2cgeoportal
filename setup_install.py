import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = "c2cgeoportal, generic gis protail made by camptocamp"

setup(name='c2cgeoportal',
      version='0.2',
      description='Templates for c2cgeoportal',
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
      zip_safe=False,
      install_requires=[
        'PasteScript',
#        'papyrus_ogcproxy',
#        'sqlahelper',
#        'pyramid_tm',
      ],
      entry_points = {
        'paste.paster_create_template': [
            'c2cgeoportal_create = paste_templates:TemplateCreate',
            'c2cgeoportal_update = paste_templates:TemplateUpdate',
        ],
      }
)

