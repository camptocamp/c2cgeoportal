from setuptools import setup

version = "0.1.0"
readme = open('README.md').read()

setup(
    name="c2cgeoportal_commons",
    packages=["c2cgeoportal_commons"],
    version=version,
    description="c2cgeoportal commons",
    long_description=readme,
    include_package_data=True,
    author="Camptocamp",
    author_email="info@camptocamp.com",
    install_requires=[
        "sqlahelper",
        "papyrus",
    ],
    extras_require={
        'testing': [
            'psycopg2',
            'pytest',
            'pytest-cov',
            #'pydevd',
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
