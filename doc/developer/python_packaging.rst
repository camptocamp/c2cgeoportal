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
    ...

c2cgeoportal releases
---------------------

Releasing c2cgeoportal means creating a source distribution of c2cgeoportal and
uploading it to http://pypi.camptocamp.net/internal-pypi/index/c2cgeoportal.

``pypirc`` configuration
~~~~~~~~~~~~~~~~~~~~~~~~

To be able to upload distributions to the Camptocamp internal PyPI it is
required to have an appropriate (e.g. ``[c2c-internal]``) section in
``~/.pypirc``::

    [distutils]
    index-servers =
        c2c-internal

    [c2c-internal]
    username:<pypi.camptocamp.net/internal-pypi_username>
    password:<pypi.camptocamp.net/internal-pypi_password>
    repository:http://pypi.camptocamp.net/internal-pypi/simple

Prepare your repository
~~~~~~~~~~~~~~~~~~~~~~~

Before creating a version or a release you should have a clean repository,
then reset non commited changes and remove all untracked files and directories:

.. prompt:: bash

    git reset --hard
    git clean -f -d

Build c2cgeoportal
~~~~~~~~~~~~~~~~~~

Creating c2cgeoportal distributions requires building c2cgeoportal. This
is done using Buildout:

.. prompt:: bash

    buildout/bin/buildout -c buildout_dev.cfg

Create and upload development distributions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We want to be able to create and upload *development distributions*.

To create and upload a development distribution just run the following
command:

.. prompt:: bash

    buildout/bin/python setup.py sdist upload -r c2c-internal

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
distributions* specific options are required on the command line:

.. prompt:: bash

    buildout/bin/python setup.py egg_info --no-date --tag-build "" sdist upload -r c2c-internal

The important note of the previous section applies here too, obviously.

Then tag the code that's released:

.. prompt:: bash

    git tag <c2cgeoportal_version>
    git push origin <c2cgeoportal_version> 

``origin`` or whatever name you have for the github.com/camptocamp/c2cgeoportal remote.

.. note::

    Once a release distribution has been uploaded, you should bump the
    current version of c2cgeoportal in ``setup.py``.
    Actually, next development version should have a higher version
    than the current stable one.

Release checklist
~~~~~~~~~~~~~~~~~

Before releasing:

 * make sure all the tests pass
 * make sure the version number is correct in ``setup.py``
 * make sure you don't have uncommitted/unpushed changes
