.. _developer_build_release:

Create a new release
====================

Vocabulary
----------

On this page I use the word ``version`` for a major version of MapFish
Geoportal (1.6), and the word ``release`` for each step in this version
(1.6.0rc1, 1.6.0, 1.6.1, ...).

``MapFish Geoportal`` is the pack that includes CGXP and c2cgeoportal,
from start of 2014 both projects will synchronize their major versions.

Then ``<release>`` can be ``1.6.0rc1`` for the first release candidate
of the version ``1.6.0``, ``1.6.0`` for the final release, ``1.6.1`` for
the first bug fix release, and ``<version>`` can be ``1.6``, ``2.0``, ...

CGXP
----

New version
~~~~~~~~~~~

For each version we create a new branch (at least at the final release):

.. prompt:: bash

    git fetch
    git checkout master
    git reset --hard origin/master
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

    git fetch
    git checkout <version>
    git reset --hard origin/<version>
    git tag <release>
    git push origin <release>

c2cgeoportal
------------

New version
~~~~~~~~~~~

Checkout the code:

.. prompt:: bash

    git fetch
    git checkout master
    git reset --hard origin/master

Get the localisation from Transifex:

.. prompt:: bash

    make transifex-get

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

Create a new Transifex resource:

    * Go to URL: https://www.transifex.com/camptocamp/geomapfish/content/
    * Click on "Add a resource"
    * Select the ``.pot`` file
    * The name should be something like "c2cgeoportal-2_0" (with the right version)
    * Click on "Create a resource"
    * Run `make transifex-init`

Then continue by creating the release.

New release
~~~~~~~~~~~

Checkout the code:

.. prompt:: bash

    git fetch
    git checkout <version>
    git reset --hard origin/<version>

Tag the new release:

.. prompt:: bash

    git tag <release>
    git push origin <release>

Notes about Travis
~~~~~~~~~~~~~~~~~~

When you push a tag with the pattern ``^[0-9]+\.[0-9]+\..+$``
a new release will automatically be created on Travis CI.

Post release tasks
------------------

When a new release or a new version is done you should do the following tasks:

* Merge the release changes (on ``cgxp`` and on ``c2cgeoportal``)
  to the upper branches i.e.: ``1.6`` => ``2.0``, ``2.0`` => ``master``.

  .. note::

     On ``c2cgeoportal`` merge see if an alembic merge should be done:

     .. prompt:: bash

        .build/venv/bin/alembic \
            -c c2cgeoportal/tests/functional/alembic.ini \
            heads
        .build/venv/bin/alembic \
            -c c2cgeoportal/tests/functional/alembic_static.ini \
            heads

     If yes create the merge with:

     .. prompt:: bash

        .build/venv/bin/alembic \
            -c c2cgeoportal/tests/functional/alembic[_static].ini \
            merge -m "Merge <src> and <dst> branches" \
            <rev 1> <rev 2>

     Remove the import and replace the core of the method by ``pass`` in the generated file.

     And finally add the new file.

* Upgrade the demo in your home folder with ``c2ctool``.
* Update the demo on the main folder with:

  .. prompt:: bash

    sudo -u sigdev make -f demo.mk update
    sudo -u sigdev make -f demo.mk build

* Test the demo.
* Move all the open issues to a new milestone and close the current milestone
  in `cgxp <https://github.com/camptocamp/cgxp/milestones>`
  and in `c2cgeoportal <https://github.com/camptocamp/c2cgeoportal/milestones>`.
* Send a release email to the ``geomapfish@googlegroups.com``
  and ``geospatial@lists.camptocamp.com`` mailing lists.
