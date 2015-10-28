.. _developer_python_packaging:

Python Packaging
================

Mirror
------

The mirror is available at this *Python Package Index* (PyPI): http://pypi.camptocamp.net/pypi.
It's a mirror of the `official PyPI <http://pypi.python.org>`_.
It is based on `collective.eggproxy <http://pypi.python.org/pypi/collective.eggproxy>`_.
We use this mirror as a proxy cache for our external dependencies.

Package
-------

c2cgeoportal is available as a wheel on the
`GitHub Releases <https://github.com/camptocamp/c2cgeoportal/releases>`_.

The packages will be done by `Travis <http://travis-ci.org/>`_ on new commit
on the ``master`` branch or on a new tag of the format ``x.y.z``.
