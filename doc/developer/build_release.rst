.. _developer_build_release:

Create a new release
====================

Vocabulary
----------

On this page, we use the word ``version`` for a major version of GeoMapFish
(2.0), and the word ``release`` for each step in this version
(2.0.0rc1, 2.0.0, 2.0.1, ...).

``MapFish Geoportal`` is the pack that includes ngeo and c2cgeoportal;
since 2014, both projects are synchronizing their major versions.

For example, ``<release>`` can be ``2.0.0rc1`` for the first release candidate
of the version ``2.0``, ``2.0.0`` for the final release, ``2.0.1`` for
the first bug fix release, and ``<version>`` can be ``2.0``, ``2.1``, ...

.. _developer_build_release_pre_release_task:

Tasks to do
-----------

For ``ngeo``,
`follows the documentation on ngeo <https://github.com/camptocamp/ngeo/blob/master/docs/developer-guide.md#create-a-new-stabilization-branch>`_.


On branch creation (start of the integration phase):

* Create the new branch on demo
* Create the new branch
* Use the ``ngeo`` package linked to the new branch
* Create the new Transifex resources
* Update the master branch
* Protect the new branch
* Configure the rebuild
* Verify that the change log creation is working
* Configure the branch on the status dashboard

On release creation:

* Reset the change log
* Do the tags
* Publish it
* Create the new demo
* Use the new demo

.. note::

   All changes should be committed.

Create the new branch on demo
-----------------------------

You should create the new version branch.

You should set the default branch to the new branch.

On the new branch you should copy the file ``.github/workflows/upgrade-<new version>.yaml`` to
``.github/workflows/upgrade-<next version>.yaml`` and update the versions in the new file:

.. code::

   name: Upgrade <version>

   on:
     repository_dispatch:
       types:
         - geomapfish_<version>_updated

       name: Upgrade <version>

           branch:
             - prod-<version>

Create the new branch
---------------------

You should create the new version branch.

In the files ``.github/workflows/main.yaml`` and ``.github/workflows/qgis.yaml`` set ``MAIN_BRANCH`` to
  ``<new version>``.

Use the ``ngeo`` package linked to the new branch
-------------------------------------------------

In ``c2cgeoportal`` new version branch, in the file ``geoportal/package.json``, set the ``ngeo`` version to
``version-<new version>-latest``.

Create the new Transifex resources
----------------------------------

Run:

.. prompt:: bash

    tx pull --source --branch=<version> --force \
        --resources=geomapfish.c2cgeoportal_geoportal,geomapfish.c2cgeoportal_admin
    tx pull --translations --branch=<version> --force --all \
        --resources=geomapfish.c2cgeoportal_geoportal,geomapfish.c2cgeoportal_admin

    tx push --branch=<next version> --source --force \
        --resources=geomapfish.c2cgeoportal_geoportal,geomapfish.c2cgeoportal_admin
    tx push --branch=<next version> --translation --force \
        --resources=geomapfish.c2cgeoportal_geoportal,geomapfish.c2cgeoportal_admin

Update the master branch
-------------------------

Configure the rebuild
---------------------

Copy the file ``.github/workflows/main.yaml`` from new version branch to master branch as
``.github/workflows/rebuild-<new version>.yaml`` and do the following changes:

.. code:: diff

   - name: Continuous integration
   + name: Rebuild <new version>

     on:
   -   push:
   -   pull_request:
   +   schedule:
   +     - cron: "30 3 * * *"

     jobs:
   -   not-failed-backport:
   -     ...

   -     name: Continuous integration
   +     name: Rebuild <new version>

   -     if: "!startsWith(github.event.head_commit.message, '[skip ci] ')"

   +     strategy:
   +       fail-fast: false
   +       matrix:
   +         branch:
   +           - 'x.y'


        env:
   -      MAIN_BRANCH: master
   +      MAIN_BRANCH: <new version>

           - uses: actions/checkout@v2
             with:
   +          ref: ${{ env.MAIN_BRANCH }}

   -       # Test Upgrade
   -       ...
   -       - run: ci/test-upgrade cleanup ${HOME}/workspace

   -       - name: Update the changelog
   -         ...
   -       - run: git diff CHANGELOG.md

   -   - name: Push version and changelog
   -     ...

       - name: Publish
         run: >
           c2cciutils-publish
             --docker-versions=${{ steps.version.outputs.versions }}
             --snyk-version=${{ steps.version.outputs.snyk_version }}
   +         --type=rebuild
   -     if: >
   -       env.HAS_SECRETS == 'HAS_SECRETS'
   -       && steps.version.outputs.versions != ''
   -
   -       - name: Notify demo
   -         ...
   -
   -       - name: Publish to Transifex
   -         ...
   -
   -       - name: Publish documentation to GitHub.io
   -         ...


Copy the files ``.github/workflows/qgis.yaml`` from new version branch to master branch
as ``.github/workflows/rebuild-qgis-<new version>.yaml`` and do the following changes:

.. code:: diff

   - name: QGIS build
   + name: QGIS rebuild <new version>

     on:
   -   push:
   -   pull_request:
   +   schedule:
   +     - cron: "30 3 * * *"

   -     name: QGIS build
   +     name: QGIS rebuild <new version>

   -     if: "!startsWith(github.event.head_commit.message, '[skip ci] ')"

         strategy:
           fail-fast: false
           matrix:
             version:
               ...
   +         branch:
   +           - 'x.y'

         env:
   -       MAIN_BRANCH: master
   -       MAJOR_VERSION: x.y
   +       MAIN_BRANCH: ${{ matrix.branch }}
   +       MAJOR_VERSION: ${{ matrix.branch }}

           - uses: actions/checkout@v1
             with:
              fetch-depth: 0
   +          ref: ${{ env.MAIN_BRANCH }}

      - name: Publish
        run: >
          c2cciutils-publish
            --group=qgis-${{ matrix.version }}
            --docker-versions=${{ steps.version.outputs.versions }}
            --snyk-version=${{ steps.version.outputs.snyk_version }}
   +        --type=rebuild
   -     if: >
   -       github.ref != format('refs/heads/{0}', env.MAIN_BRANCH)
   -       && github.repository == 'camptocamp/c2cgeoportal'
   -   - name: Publish version branch
   -     ...

Copy the file ``.github/workflows/main.yaml`` from new version branch to master branch as
``.github/workflows/ngeo-<new version>.yaml`` and do the following changes:

.. code:: diff

   - name: Continuous integration
   + name: Update ngeo <new version>

     on:
   -   push:
   +   repository_dispatch:
   +     types:
   +     - ngeo_<new version>_updated

   -     name: Continuous integration
   +     name: Update ngeo <new version>

   -    if: "!startsWith(github.event.head_commit.message, '[skip ci] ')"

         env:
   -       MAIN_BRANCH: master
   -       MAJOR_VERSION: x.y
   +       MAIN_BRANCH: x.y
   +       MAJOR_VERSION: x.y

        jobs:
   -      not-failed-backport:
   -        ...


   -       - uses: actions/checkout@v2
   -         with:
   -           fetch-depth: 0
   -           token: ${{ secrets.GOPASS_CI_GITHUB_TOKEN }}
   -         if: env.HAS_SECRETS == 'HAS_SECRETS'
           - uses: actions/checkout@v2
             with:
               fetch-depth: 0
   +           ref: ${{ env.MAIN_BRANCH }}
             if: env.HAS_SECRETS != 'HAS_SECRETS'


      - name: Publish
        run: >
          c2cciutils-publish
            --docker-versions=${{ steps.version.outputs.versions }}
            --snyk-version=${{ steps.version.outputs.snyk_version }}
   +        --type=rebuild

   -       - name: Publish to Transifex
   -         ...
   -
   -       - name: Publish documentation to GitHub.io
   -         ...


And also remove all the `if` concerning the following tests:

- ``github.ref != format('refs/heads/{0}', env.MAIN_BRANCH)``
- ``github.repository == 'camptocamp/c2cgeoportal'``
- ``env.HAS_SECRETS == 'HAS_SECRETS`` (optional)

Configure the new branch
------------------------

In the file ``.github/workflows/main.yaml`` and ``.github/workflows/qgis.yaml`` set ``MAJOR_VERSION`` to
  ``<next version>``.

Configure the audit
-------------------

Add the new version branch in the ``.github/workflows/audit.yaml`` file.

Configure the branch on the status dashboard
--------------------------------------------

Add the new branch for the demo, ngeo and c2cgeoportal in the file
`scripts/status.yaml <https://github.com/camptocamp/geospatial-dashboards/blob/master/ci/status.yaml>`_.

Reset the change log
--------------------

On the ``c2cgeoportal`` new version branch:

* Empty the file ``CHANGELOG``
* Set the content of the file ``ci/changelog.yaml`` to:

  .. code:: yaml

     commits:
       c2cgeoportal: {}
       ngeo: {}
     pulls:
       c2cgeoportal: {}
       ngeo: {}
     releases: []

Security information
--------------------

On the master branch, update the file ``SECURITY.md`` with the security information by adding:

.. code::

  | x.y+1 | To be defined |

Backport label
--------------

Create the new back port label named ``backport_<new_version>``.

Protect branch
--------------

In GitHub project settings, protect the new branch with the same settings as the master branch.

Publish it
----------

Send a release email to the ``geomapfish@googlegroups.com`` and
``geomapfish-dev@lists.camptocamp.com`` mailing lists.


Create the new demo
-------------------

Create the new demo on Kubernetes

Use the new demo
----------------

On ``ngeo`` master branch change all the URL
from ``https://geomapfish-demo-<new version>.camptocamp.com``
to ``https://geomapfish-demo-<next version>.camptocamp.com``.
