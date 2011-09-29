try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

setup(
    name='project',
    version='1.0',
    description='A c2cgeoportal project',
    author='camptocamp',
    author_email='info@camptocamp.com',
    url='http://www.camptocamp.com/geospatial-solutions',
    install_requires=[
        'PasteScript',
        'c2cgeoportail',
    ],
    packages=find_packages(exclude=['ez_setup']),
    include_package_data=True,
    zip_safe=False,
    entry_points={
        'paste.app_factory': [
            'main = project:main',
        ],
        'console_scripts': [
            'create_db = project.scripts.create_db:main',
        ],
    },
)
