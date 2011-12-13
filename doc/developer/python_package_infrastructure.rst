.. _developer_python_package_infrastructure:

Python Package Infrastructure
=============================

We rely on two *Python Package Index*: http://pypi.camptocamp.net/pypi and
http://pypi.camptocamp.net/internal-pypi/index.

http://pypi.camptocamp.net/pypi is a mirror of the official Python Package
Index, http://pypi.python.org. It is based on `collective.eggproxy
<http://pypi.python.org/pypi/collective.eggproxy>`_. We use this mirror as
a proxy cache for our external dependencies.

http://pypi.camptocamp.net/internal-pypi/index includes ``c2cgeoportal`` and
``tileforge`` eggs (and possibly other private eggs in the future). It is based
on `CheesePrism <https://github.com/SurveyMonkey/CheesePrism>`_. To access this
Package Index a login/password is required.

The buildout configurations of c2cgeoportal applications use ``index``
and ``find-links`` to reference these Package Index::

    [buildout]
    ...
    index = http://pypi.camptocamp.net/pypi
    find-links = http://pypi.camptocamp.net/internal-pypi/index/c2cgeoportal
                 http://pypi.camptocamp.net/internal-pypi/index/tileforge
    ...

And they use the `lovely.buildouthttp
<http://pypi.python.org/pypi/lovely.buildouthttp>`_ buildout extension for the
HTTP Authentication.
