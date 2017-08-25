from setuptools import setup

url = ""
version = "0.1.0"
readme = open('README.rst').read()

setup(
    name="c2cgeoportal_commons",
    packages=["c2cgeoportal_commons"],
    version=version,
    description="c2cgeoportal commons",
    long_description=readme,
    include_package_data=True,
    author="c2c",
    author_email="info@camptocamp.com",
    url=url,
    install_requires=[
        "sqlahelper",
        "papyrus",
    ],
    download_url="{}/tarball/{}".format(url, version),
    license="MIT",
    entry_points={
        'console_scripts': [
            'initialize_db_main = c2cgeoportal_commons.scripts.initializedb:main',
        ],
    },
)
