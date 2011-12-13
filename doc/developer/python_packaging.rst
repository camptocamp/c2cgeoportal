.. _developer_python_packaging:

Python Packaging
================

Infrastructure
--------------

We rely on two *Python Package Index* (PyPI): http://pypi.camptocamp.net/pypi
and http://pypi.camptocamp.net/internal-pypi/index.

http://pypi.camptocamp.net/pypi is a mirror of the official PyPI,
http://pypi.python.org. It is based on `collective.eggproxy
<http://pypi.python.org/pypi/collective.eggproxy>`_. We use this mirror as
a proxy cache for our external dependencies.

http://pypi.camptocamp.net/internal-pypi/index includes ``c2cgeoportal`` and
``tileforge`` eggs (and possibly other private eggs in the future). It is based
on `CheesePrism <https://github.com/SurveyMonkey/CheesePrism>`_. To access this
PyPI a login/password is required.

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

c2cgeoportal releases
---------------------

Releasing c2cgeoportal means creating a source distribution of c2cgeoportal and
uploading it to http://pypi.camptocamp.net/internal-pypi/index/c2cgeoportal.

``pypirc`` configuration
~~~~~~~~~~~~~~~~~~~~~~~~

To be able to upload distributions to the Camptocamp internal PyPI it is
required to have an appropriate (e.g. ``[internal]``) section in
``~/.pypirc``::

    $ cat ~/.pypirc

    [distutils]
    index-servers =
        pypi
        c2c-internal

    [pypi]
    username:<pypi.python.org_username>
    password:<pypi.python.org_password>

    [c2c-internal]
    username:<pypi.camptocamp.net/internal-pypi_username>
    password:<pypi.camptocamp.net/internal-pypi_password>
    repository:http://pypi.camptocamp.net/internal-pypi/simple

Create and upload development distributions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We want to be able to create and upload *development distributions*.

To create and upload a development distribution just run the following
command::

    $ python setup.py sdist upload -r c2c-internal

As you can see the name of a development distribution includes a ``dev``
*pre-release* tag and a date *post-release* tag. This is by convention.

``c2c-internal`` in the name of the section you added in ``~/.pypirc`` for the
Camptocamp internal index.

.. important::

    Never upload distributions including code that is not in the master branch
    of the GitHub repository. So push before distributing!

Create and upload release distributions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By default ``setup.py sdist`` produces development distributions (see
the ``[egg_info]`` options in ``setup.cfg``). To create *release
distributions* specific options are required on the command line::

    $ python setup.py egg_info --no-date --tag-build "" dist upload -r c2c-internal

The important note of the previous section applies here too, obviously.

Release checklist
~~~~~~~~~~~~~~~~~

Before releasing:

 * make sure all the tests pass
 * make sure the version number is correct in ``setup.py``
 * make sure you don't have uncommitted/unpushed changes
