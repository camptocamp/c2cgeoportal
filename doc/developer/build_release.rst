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

.. prompt:: bash

    NEW_VERSION=x.y
    git checkout master
    git pull
    git checkout -b "${NEW_VERSION}"
    git push --set-upstream origin "${NEW_VERSION}"
    git push origin "${NEW_VERSION}"


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

    NEW_VERSION=x.y
    NEXT_VERSION=x.y+1
    tx pull --source --branch="${NEW_VERSION}" --force \
        --resources=geomapfish.c2cgeoportal_geoportal,geomapfish.c2cgeoportal_admin
    tx pull --translations --branch="${NEW_VERSION}" --force --all \
        --resources=geomapfish.c2cgeoportal_geoportal,geomapfish.c2cgeoportal_admin

    tx push --branch="${NEXT_VERSION}" --source --force \
        --resources=geomapfish.c2cgeoportal_geoportal,geomapfish.c2cgeoportal_admin
    tx push --branch="${NEXT_VERSION}" --translation --force \
        --resources=geomapfish.c2cgeoportal_geoportal,geomapfish.c2cgeoportal_admin

Create a pull request
---------------------

Create a pull request to update the new version branch.

.. prompt:: bash

    NEW_VERSION=x.y
    git checkout -b "setup-${NEW_VERSION}"
    pre-commit run --files=geoportal/package.json npm-lock
    git add geoportal/package.json geoportal/package-lock.json .github/workflows/main.yaml .github/workflows/qgis.yaml
    git commit -m "Use ngeo version ${NEW_VERSION}"
    git push --set-upstream origin "setup-${NEW_VERSION}"

  Create the pull request on GitHub.

Update the master branch
-------------------------

.. prompt:: bash

    git checkout master
    git pull

Copy the file ``.github/workflows/main.yaml`` from new version branch to master branch as
``.github/workflows/ngeo-<new version>.yaml`` and do the following changes:

.. code:: diff

   -name: Continuous integration
   +name: Update ngeo <new version>

    on:
   -  push:
   +  repository_dispatch:
   +    types:
   +    - ngeo_<new version>_updated

    jobs:
   -  not-failed-backport:
   -    ...

      build:
        ...
   -    name: Continuous integration
   +    name: Update ngeo <new version>
        ...
   -    if: "!startsWith(github.event.head_commit.message, '[skip ci] ')"

        env:
   -      MAIN_BRANCH: master
   -      MAJOR_VERSION: x.y
   +      MAIN_BRANCH: x.y
   +      MAJOR_VERSION: x.y

        steps:
          ...

   -      - uses: actions/checkout@v2
   -        with:
   -          fetch-depth: 0
   -          token: ${{ secrets.GOPASS_CI_GITHUB_TOKEN }}
   -        if: env.HAS_SECRETS == 'HAS_SECRETS'
          - uses: actions/checkout@v2
            with:
              fetch-depth: 0
   +          ref: ${{ env.MAIN_BRANCH }}
            if: env.HAS_SECRETS != 'HAS_SECRETS'

          ...

   +      - run: cd geoportal && npm update
          - run: scripts/get-version --auto-increment --github
            id: version

          ...

          - run: git diff CHANGELOG.md
   +      - run: |
   +          git add geoportal/package-lock.json
   +          git commit -m "Update used ngeo version"

          ...

          - name: Publish
            run: >
              c2cciutils-publish
              --docker-versions=${{ steps.version.outputs.versions }}
              --snyk-version=${{ steps.version.outputs.snyk_version }}
   +          --type=rebuild

   -      - name: Publish version branch to pypi
   -        ...
   -
   -      - name: Publish to Transifex
   -        ...
   -
   -      - name: Publish documentation to GitHub.io
   -        ...


And also remove all the `if` concerning the following tests:

- ``github.ref != format('refs/heads/{0}', env.MAIN_BRANCH)``
- ``env.HAS_SECRETS == 'HAS_SECRETS`` (optional)

Configure the new branch
------------------------

In the file ``.github/workflows/main.yaml`` and ``.github/workflows/qgis.yaml`` set ``MAJOR_VERSION`` to
  ``<next version>``.

Reset the change log
--------------------

On the ``c2cgeoportal`` new version branch:

* Empty the file ``CHANGELOG.md``
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

Create the pull request
-----------------------

.. prompt:: bash

    NEXT_VERSION=x.y
    git add -A
    git add .github/workflows/ngeo-*.yaml
    git checkout -b "start-${NEXT_VERSION}"
    git commit -m "Start the version ${NEXT_VERSION}"
    git push --set-upstream origin "start-${NEXT_VERSION}"

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
