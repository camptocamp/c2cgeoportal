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

.. _developer_build_release_pre_release_task:

Pre release task
----------------

Before doing a release you should merge all the previous branch on this one:

* Merge the release changes (on ``ngeo`` and on ``c2cgeoportal``)
  to the upper branches i.e.: ``1.6`` => ``2.2``, ..., ``2.3`` => ``2.4``.

  .. note::

     On ``c2cgeoportal`` merge see if an alembic merge should be done:

     .. prompt:: bash

        ./docker-compose-run alembic \
            --config=tests/functional/alembic.ini \
            --name=main heads
        ./docker-compose-run alembic \
            --config=tests/functional/alembic.ini \
            --name=static heads

     If yes create the merge with:

     .. prompt:: bash

        ./docker-compose-run alembic \
            --config=tests/functional/alembic.ini --name=[main|static] \
            merge --message="Merge <src> and <dst> branches" \
            <rev 1> <rev 2>

     Remove the import and replace the core of the method by ``pass`` in the generated file.

     And finally add the new file.

ngeo
----

`For ngeo see here <https://github.com/camptocamp/ngeo/blob/master/docs/developer-guide.md#create-a-package-on-npm>`_.

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

    docker build --tag=camptocamp/geomapfish-build-dev docker/build
    ./docker-run make transifex-get

For each version we create a new branch (at the latest at the final release):

.. prompt:: bash

    git checkout -b <version>
    git push origin <version>

Change the version in the following files:
 * ``.travis.yml`` (``MAIN_BRANCH``, ``MAJOR_VERSION``)
 * ``Jenkinsfile`` (``MAIN_BRANCH``, ``MAJOR_VERSION``)
 * ``Makefile`` (``MAIN_BRANCH``, ``MAJOR_VERSION``)
 * ``docker-run`` (``version``)

Commit your changes:

.. prompt:: bash

    git add .travis.yml Jenkinsfile Makefile docker-run
    git commit -m "Create the version <version> branch"

Go back to the master branch:

.. prompt:: bash

    git checkout master
    git merge <version>

Change back the version in the following files:
 * ``.travis.yml`` (``MAIN_BRANCH``, ``MAJOR_VERSION``)
 * ``Jenkinsfile`` (``MAIN_BRANCH``, ``MAJOR_VERSION``)
 * ``Makefile`` (``MAIN_BRANCH``, ``MAJOR_VERSION``)
 * ``docker-run`` (``version``)

Commit your changes:

.. prompt:: bash

    git add .travis.yml Jenkinsfile Makefile docker-run
    git commit -m "Start version <version + 1>"

Push your changes:

.. prompt:: bash

    git push origin <version> master

Create a new Transifex resource:

.. prompt:: bash

    rm .tx/config
    ./docker-run rm /build/c2ctemplate-cache.yaml
    ./docker-run make transifex-init

Then continue by creating the release.

Do the new release
~~~~~~~~~~~~~~~~~~

Checkout the code:

.. prompt:: bash

    git fetch
    git checkout <version>
    git reset --hard origin/<version>

Tag the new release:

.. prompt:: bash

    git tag <release>
    git push origin <release>

Run a new job for the <version> branch on Jenkins.

.. note::

    It's possible to do a version only on the latest commit on a branch,
    If you relay need to do that, you should create a new branch.

Notes about Travis
~~~~~~~~~~~~~~~~~~

When you push a tag with the pattern ``^[0-9]+\.[0-9]+\..+$``
a new release will automatically be created on Travis CI.

Post release tasks
------------------

When a new release or a new version is done you should do the following tasks:

* Merge the version into the upper one to the master i.e.: ``2.4`` => ``2.5``, ``2.5`` => ``master``.

See :ref:`developer_build_release_pre_release_task` for more information.

* Upgrade the demo in your home folder, see :ref:`integrator_upgrade_application`.
* Some specific things for the demo:
  `UPGRADE.rst <https://github.com/camptocamp/demo_geomapfish/blob/2.4/UPGRADE.rst>_`.

For non dev release
-------------------

* Rename the milestone on `c2cgeoportal <https://github.com/camptocamp/c2cgeoportal/milestones>`_
  and on `ngeo <https://github.com/camptocamp/ngeo/milestones>`_ from ``x.y`` to ``x.y.z``.
* Create again the milestone on `c2cgeoportal <https://github.com/camptocamp/c2cgeoportal/milestones>`_
  and on `ngeo <https://github.com/camptocamp/ngeo/milestones>`_ for ``x.y``.
* Move all the open issues to the new milestone and close the current milestone
  in `ngeo <https://github.com/camptocamp/ngeo/milestones>`_
  and in `c2cgeoportal <https://github.com/camptocamp/c2cgeoportal/milestones>`_.
* Send a release email to the ``geomapfish@googlegroups.com``
  and ``gmf2@lists.camptocamp.com`` mailing lists.
