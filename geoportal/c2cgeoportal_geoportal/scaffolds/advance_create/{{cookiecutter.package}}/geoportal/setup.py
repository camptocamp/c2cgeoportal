#!/usr/bin/env python3

from setuptools import find_packages, setup

setup(
    name="{{cookiecutter.package}}_geoportal",
    version="1.0",
    description="{{cookiecutter.package}}, a c2cgeoportal project",
    author="{{cookiecutter.package}}",
    author_email="info@{{cookiecutter.package}}.com",
    url="https://www.{{cookiecutter.package}}.com/",
    install_requires=[
        "c2cgeoportal_geoportal",
        "c2cgeoportal_admin",
    ],
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    entry_points={
        "paste.app_factory": [
            "main = {{cookiecutter.package}}_geoportal:main",
        ],
        "console_scripts": [],
    },
)
