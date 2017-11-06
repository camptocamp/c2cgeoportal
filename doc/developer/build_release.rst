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

`For ngeo see here <https://github.com/camptocamp/ngeo/blob/master/docs/developer-guide.md#create-a-package-on-npm>_`.

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

* Merge the release changes (on ``ngeo`` and on ``c2cgeoportal``)
  to the upper branches i.e.: ``1.6`` => ``2.0``, ``2.0`` => ``master``.

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

* Upgrade the demo in your home folder with ``make upgrade``.
* Update the demo on the test server in the main folder with:

  .. prompt:: bash

    sudo -u sigdev make --makefile=demo.mk update
    sudo -u sigdev make --makefile=demo.mk build

* Test the `demo <http://testgmf.sig.cloud.camptocamp.net/>_`.
* Deploy on the demo server with:

  .. prompt:: bash

     sudo -u deploy deploy -r deploy/deploy.cfg demo_server

* Rename the milestone on `c2cgeoportal <https://github.com/camptocamp/c2cgeoportal/milestones>_`
  and on `ngeo <https://github.com/camptocamp/ngeo/milestones>_` from ``x.y`` to ``x.y.z``.
* Create again the milestone on `c2cgeoportal <https://github.com/camptocamp/c2cgeoportal/milestones>_`
  and on `ngeo <https://github.com/camptocamp/ngeo/milestones>_` for ``x.y``.
* Move all the open issues to the new milestone and close the current milestone
  in `ngeo <https://github.com/camptocamp/ngeo/milestones>_`
  and in `c2cgeoportal <https://github.com/camptocamp/c2cgeoportal/milestones>_`.
* Send a release email to the ``geomapfish@googlegroups.com``
  and ``gmf2@lists.camptocamp.com`` mailing lists.
