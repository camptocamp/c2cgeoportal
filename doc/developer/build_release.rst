.. _developer_build_release:

Create a new release
====================

Vocabulary
----------

On this page, we use the word ``version`` for a major version of MapFish
Geoportal (2.0), and the word ``release`` for each step in this version
(2.0.0rc1, 2.0.0, 2.0.1, ...).

``MapFish Geoportal`` is the pack that includes ngeo and c2cgeoportal;
since 2014, both projects are synchronizing their major versions.

For example, ``<release>`` can be ``2.0.0rc1`` for the first release candidate
of the version ``2.0``, ``2.0.0`` for the final release, ``2.0.1`` for
the first bug fix release, and ``<version>`` can be ``2.0``, ``2.1``, ...

.. _developer_build_release_pre_release_task:

Tasks to do
-----------

On branch creation (start of the integration phase):

* Create and initialise the branches
* Protect the new branches
* Configure the rebuild
* Use the ``ngeo`` package linked to the branch
* Verify that the changelog creation is working

On release creation:

* Reset the changelog
* Do the tags
* Publish it
* Create the new demo
* Use the new demo

.. note::

   All changes should be committed.

Create the branches
-------------------

On the demo you should create the new version branch.

On ``ngeo`` you should create the new version branch.

On ``c2cgeoportal`` you should create the new version branch.

On the demo GitHub repository you should set the default branch to the new branch.

On the new branch of the demo you should copy the file ``.github/workflows/upgrade-<new version>.yaml`` to
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
             - prod-<version>-simple

On the new version branch:

- in the files ``.github/workflows/main.yaml`` and  ``.github/workflows/qgis.yaml`` set ``MAIN_BRANCH`` to
  ``<new version>``.

On the master branch:

- add the new branch for the demo, ngeo and c2cgeoportal in the file ``scripts/status.yaml``.
- in the file ``.github/workflows/main.yaml`` and  ``.github/workflows/qgis.yaml`` set ``MAJOR_VERSION`` to
  ``<next version>``.
- in the files ``.github/workflows/audit.yaml`` and the new branch.

Configure the rebuild
---------------------

On ``c2cgeoportal`` copy the file ``.github/workflows/main.yaml`` from new version branch to master branch as
``.github/workflows/rebuild-<new version>.yaml`` and do the following changes:

.. code:: diff

   - name: Continuous integration
   + name: Rebuild <new version>

     on:
   -   push:
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

           - uses: actions/checkout@v1
             with:
   +          ref: ${{ env.MAIN_BRANCH }}

   -       # Test Upgrade
   -       ...
   -       - run: ci/test-upgrade cleanup ${HOME}/workspace

       - name: Publish feature branch
   -     run: |
   -       c2cciutils-publish
   -       c2cciutils-publish --group=full
   +       c2cciutils-publish --type=rebuild
   -     if: >
   -       github.ref != format('refs/heads/{0}', env.MAIN_BRANCH)
   -       && github.repository == 'camptocamp/c2cgeoportal'
   -   - name: Publish version branch
   -     ...

   -       - name: Update the changelog
   -         ...
   -       - run: git diff CHANGELOG.md

   -       - name: Push version and changelog
   -         ...

   -       - name: Publish to Transifex
   -         ...
   -
   -       - name: Publish documentation to GitHub.io
   -         ...
   -
   -       - name: Notify demo
   -         ...


On ``c2cgeoportal`` copy the files ``.github/workflows/qgis.yaml`` from new version branch to master branch
as ``.github/workflows/rebuild-qgis-<new version>.yaml`` and do the following changes:

.. code:: diff

   - name: QGIS
   + name: QGIS rebuild <new version>

     on:
   -   push:
   +   schedule:
   +     - cron: "30 3 * * *"

   -     name: QGIS
   +     name: QGIS rebuild <new version>

   -     if: "!startsWith(github.event.head_commit.message, '[skip ci] ')"

         strategy:
           fail-fast: false
           matrix:
   +         branch:
   +           - 'x.y'

         env:
   -       MAIN_BRANCH: master
   -       MAJOR_VERSION: x.y
   +       MAIN_BRANCH: ${{ matrix.branch }}
   +       MAJOR_VERSION: ${{ matrix.branch }}

           - uses: actions/checkout@v1
   +         with:
   +          ref: ${{ env.MAIN_BRANCH }}

      - name: Publish feature branch
        run: |
   -       c2cciutils-publish --group=qgis-${{ matrix.version }}
   +       c2cciutils-publish --type=rebuild --group=qgis-${{ matrix.version }}
   -     if: >
   -       github.ref != format('refs/heads/{0}', env.MAIN_BRANCH)
   -       && github.repository == 'camptocamp/c2cgeoportal'
   -   - name: Publish version branch
   -     ...

On ``c2cgeoportal`` copy the file ``.github/workflows/main.yaml`` from new version branch to master branch as
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

           - uses: actions/checkout@v1
   +         with:
   +          ref: ${{ env.MAIN_BRANCH }}

   -       - name: Publish feature branch
   -         ...
   -
   -       - name: Publish to Transifex
   -         ...
   -
   -       - name: Publish documentation to GitHub.io
   -         ...

And also remove all the `if` concerning the following tests:

- `github.ref != format('refs/heads/{0}', env.MAIN_BRANCH)`
- `github.repository == 'camptocamp/c2cgeoportal'`

Configure the audit
-------------------

Add the new version branch in the ``.github/workflows/audit.yaml`` file.


Use the ``ngeo`` package linked to the branch
---------------------------------------------

In ``c2cgeoportal`` new version branch, in the file ``geoportal/package.json``, set the ``ngeo`` version to
``version-<new version>-latest``.

Reset the changelog
-------------------

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

Version check
-------------

On the <new_version> branch disable version check by adding in the ``ci/config.yaml``:

.. code:: diff

    checks:
   +  versions: False

Backport label
--------------

Create the new backport label named ``backport_<new_version>``.

Protect branch
--------------

In GitHub project settings, protect the new branch with the same settings as the master branch.

Check
-----

Run `c2cciutils-checks` on each branch before pushing to be sure that everything is OK.

Publish it
----------

Send a release email to the ``geomapfish@googlegroups.com`` and
``geomapfish-dev@lists.camptocamp.com`` mailing lists.


Create the new demo
-------------------

Create the new demo on OpenShift

Use the new demo
----------------

On ``ngeo`` master branch change all the URL
from ``https://geomapfish-demo-<new version>.camptocamp.com``
to  ``https://geomapfish-demo-<next version>.camptocamp.com``.
