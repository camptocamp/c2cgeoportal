.. _developer_build_release:

Build a new release
===================

Vocabulary
----------

On this page I use the word ``version`` for a major version of MapFish
Geoportal (1.3), and the word ``release`` for each step in this version
(1.3rc1, 1.3.0, 1.3.1, ...).

``MapFish Geoportal`` is the pack that includes CGXP and c2cgeoportal,
from start of 2014 both projects will synchronize their major versions.

Then ``<release>`` can be ``1.3rc1`` for the first release candidate
of the version ``1.3``, ``1.3.0`` for the final release, ``1.3.1`` for
the first bug fix release, and ``<version>`` can be ``1.3``, ``1.4``, ...

CGXP
----

New version
~~~~~~~~~~~

For each version we create a new branch (at least at the final release):

.. prompt:: bash

    git checkout master
    git pull origin master
    git checkout -b <version>

Go back on master:

.. prompt:: bash

    git checkout master

Add the version in the doc generator by editing the
``core/src/doc/update_online.sh`` file and add the new ``<version>``
in the ``for VERSION in`` loop.

Commit your changes:

.. prompt:: bash

    git add core/src/doc/update_online.sh
    git commit -m "Generate documentation for version <version>"

Push your changes:

.. prompt:: bash

    git push origin master
    git push origin <version>

Then continue by creating the release.

New release
~~~~~~~~~~~

Tag the new CGXP release:

.. prompt:: bash

    git checkout <version>
    git pull origin <version>
    git tag <release>
    git push origin <release>

c2cgeoportal
------------

New version
~~~~~~~~~~~

Checkout the code:

.. prompt:: bash

    git checkout master
    git pull origin master

Edit the ``doc/integrator/update_application.rst`` file to change the default version
for the ``version.cfg``.

Add and commit the changes:

.. prompt:: bash

    git add doc/integrator/update_application.rst
    git commit -m "Update the default downloaded version.cfg"

For each version we create a new branch (at the latest at the final release):

.. prompt:: bash

    git checkout -b <version>
    git push origin <version>

Go back to the master branch:

.. prompt:: bash

    git checkout master

Edit the version in the ``setup.py`` to be ``<version + 1>``.

Commit your changes:

.. prompt:: bash

    git add setup.py
    git commit -m "Start version <version + 1>"

Push your changes:

.. prompt:: bash

    git push origin master

Then continue by creating the release.

New release
~~~~~~~~~~~

Checkout the code:

.. prompt:: bash

    git checkout <version>
    git pull origin <version>

Update the version of c2cgeoportal in the
``c2cgeoportal/scaffolds/create/versions.cfg`` file to the ``<release>``.

Verify that the version in the ``setup.py`` is correct
(as the ``<release>``).

Commit your changes:

.. prompt:: bash

    git add setup.py c2cgeoportal/scaffolds/create/versions.cfg
    git commit -m "Do release <release>"

Tag the new release:

.. prompt:: bash

    git tag <release>

Edit the version in the ``setup.py`` to be ``<release + 1>``.

Commit your changes:

.. prompt:: bash

    git add setup.py
    git commit -m "Start release <release + 1>"

Push your changes:

.. prompt:: bash

    git push origin <version>
    git push origin <release>

.. note::

   When you push a tag with the pattern `^[0-9].[0-9]+.[0-9]$` a new release
   will automatically be created on Travis CI.
