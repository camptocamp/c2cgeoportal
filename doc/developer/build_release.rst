.. _developer_build_release:

Create a new release
====================

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

Edit the ``doc/integrator/update_application.rst`` file to change the default version.

Update the version of c2cgeoportal to ``<release>`` in
``c2cgeoportal/scaffolds/update/CONST_Makefile_tmpl``
(``REQUIREMENTS ?= c2cgeoportal==<release>``).


Add and commit the changes:

.. prompt:: bash

    git add doc/integrator/update_application.rst \
        c2cgeoportal/scaffolds/update/CONST_Makefile_tmpl
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

Create a new Transifex resource:

    * Go to URL: https://www.transifex.com/camptocamp/geomapfish/content/
    * Click on "Add a resource"
    * Select the ``.pot`` file
    * The name should be something like "c2cgeoportal-1_6" (with the right version)
    * Click on "Create a resource"
    * Run `make transifex-init`

Then continue by creating the release.

New release
~~~~~~~~~~~

Checkout the code:

.. prompt:: bash

    git checkout <version>
    git pull origin <version>

Update the version of c2cgeoportal to ``<release>`` in
``c2cgeoportal/scaffolds/update/CONST_versions.txt``.

Verify that the version in the ``setup.py`` is correct
(as the ``<release>``, required when we create a release candidate
or a development release).

Release w.x.y(.z)
~~~~~~~~~~~~~~~~~

Commit your changes:

.. prompt:: bash

    git add setup.py c2cgeoportal/scaffolds/update/CONST_versions.txt
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

Release candidate or development w.x.y(rc|dev)z
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In this case we don't commit the version changes in the branch.

Commit, tag and push your changes:

.. prompt:: bash

    git add setup.py c2cgeoportal/scaffolds/update/CONST_requirements.txt \
        c2cgeoportal/scaffolds/update/CONST_requirements_windows.txt
    git commit -m "Do release <release>"
    git tag <release>
    git push origin <release>

Notes about Travis
~~~~~~~~~~~~~~~~~~

When you push a tag with the pattern ``^[0-9]+.[0-9]+.[0-9]+(dev[0-9]+|rc[0-9]+|\.[0-9]+)$``
a new release will automatically be created on Travis CI.

Post release tasks
------------------

When a new release or a new version is done you should do the following tasks:

* Merge the release changes (on ``cgxp`` and on ``c2cgeoportal``)
  to the upper branches i.e.: ``1.6`` => ``2.0``, ``2.0`` => ``master``.

  .. note::

     On ``c2cgeoportal`` merge see if an alembic merge should be done:

     .. prompt:: bash

        .build/venv/bin/alembic -c c2cgeoportal/tests/functional/alembic.ini heads
        .build/venv/bin/alembic -c c2cgeoportal/tests/functional/alembic_static.ini heads

     If yes create the merge with:

     .. prompt:: bash

        .build/venv/bin/alembic -c c2cgeoportal/tests/functional/alembic[_static].ini merge \
                -m "Merge <src branch> and <dst branch> branches" \
                --branch-label <dst branch> <rev 1> <rev 2>

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
