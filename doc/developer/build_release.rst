.. _developer_build_release:

Build a new release
===================

Vocabulary
----------

On this page I use the word ``version`` for a major version of MapFish
Geoportal (1.3), and the word ``release`` for each step in this version
(1.3rc1, 1.3.0, 1.3.1, ...).

``MapFish Geoportal`` is the pack that include CGXP and c2cgeoportal,
from start of 2014 both projects will synchronize their major versions.

CGXP
----

Build a new CGXP release::

    git checkout master
    git pull origin master
    git tag <release_name>
    git push origin <release_name>


The ``<release_name>`` can be ``1.3rc1`` for the first release candidate
of the version ``1.3``, ``1.3.0`` for the final release, ``1.3.1`` for
the first bug fix release.

For each version we create a new branch (at the latest at the final release)::

    git checkout -b <version>
    git push origin <version>

c2cgeoportal
------------

Edit the ``c2cgeoportal/scaffolds/create/versions.cfg`` to set the c2cgeoportal
release version.

Build a new c2cgeopotal release::

    git checkout master
    git pull origin master
    git tag <release_name>
    git push origin <release_name>

The ``<release_name>`` can be ``1.3rc1`` for the first release candidate
of the version ``1.3``, ``1.3.0`` for the final release, ``1.3.1`` for
the first bug fix release.

For each version we create a new branch (at the latest at the final release)::

    git checkout -b <version>
    git push origin <version>

Build c2cgeoportal::

    ./buildout/bin/buildout -c buildout_dev.cfg

Create a new package::

    ./buildout/bin/python setup.py egg_info --no-date --tag-build "<tag>" sdist upload -r c2c-internal

The ``<tag>`` is ``rc1`` for the release ``1.3rc1``,
``.0`` for the release ``1.3.0``, ...
