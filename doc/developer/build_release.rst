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

The version lifecycle involves the ``ngeo``, ``c2cgeoportal``, ``demo_geomapfish`` and
``argocd-gs-gmf-apps`` repositories; when a version is added, all of them should be consistent.

.. _developer_build_release_pre_release_task:

Tasks to do
-----------

For ``ngeo``,
`follows the documentation on ngeo <https://github.com/camptocamp/ngeo/blob/master/docs/developer-guide.md#create-a-new-stabilization-branch>`_.


On branch creation (start of the integration phase):

* Create the new branch on demo
* Create the new branch
* Clean the workflows of the new branch
* Use the ``ngeo`` package linked to the new branch
* Create the new Transifex resources
* Update the master branch
* Configure the new branch
* Add the migration test from the new version
* Verify that the change log creation is working

On release creation:

* Reset the change log
* Do the tags
* Publish it
* Create the new demo
* Use the new demo

.. note::

   All changes should be committed.

   The branch protection is automatically applied by the repository rulesets
   (they match the ``refs/heads/[0-9].[0-9]`` and ``refs/heads/[0-9].[0-9][0-9]`` branches).

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

You should create the new version branch, directly from the ``master`` branch.

.. prompt:: bash

    NEW_VERSION=x.y
    git fetch origin
    git push origin origin/master:refs/heads/"${NEW_VERSION}"

In the files ``.github/workflows/main.yaml`` and ``.github/workflows/qgis.yaml`` set ``MAIN_BRANCH`` to
  ``<new version>``.

Clean the workflows of the new branch: only the workflows that are also relevant on a stabilization branch
should be kept (``main.yaml``, ``qgis.yaml``, ``tag.yaml``, ``pull-request-automation.yaml``), the ones that
only make sense on the default branch (``ngeo-*.yaml``, ``rebuild-*.yaml``, ...) should be removed.

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
------------------------

Copy the maintenance workflow of an existing version (e.g. ``.github/workflows/ngeo-<new version - 1>.yaml``)
to ``.github/workflows/ngeo-<new version>.yaml`` and update it:

* the ``name`` and the job name to ``Update ngeo <new version>``,
* the repository dispatch type to ``ngeo_<new version>_updated``,
* ``MAIN_BRANCH`` and ``MAJOR_VERSION`` to ``<new version>``,
* the ``QGIS_VERSION`` used to build the QGIS server,
* the ``ci/test-upgrade`` steps with the ones from the new version branch.

This workflow checks out the stabilization branch, updates the ``ngeo`` package, the change log and the
version, pushes the changes on the stabilization branch and republishes the images with:

.. prompt:: bash

    tag-publish --type=rebuild --version=<new version> --docker-versions=...

Configure the new branch
------------------------

In the file ``.github/workflows/main.yaml`` and ``.github/workflows/qgis.yaml`` set ``MAJOR_VERSION`` to
  ``<next version>``.

In the ``Makefile``, update the default value for ``MAJOR_VERSION``, ``MAJOR_MINOR_VERSION`` and ``VERSION``.

In the ``scripts/get-version`` file, update the default ``MAJOR_VERSION``.

In the ``scripts/updated_version`` file, update the version used to select the json output of ``npm list``.

Add the migration test from the new version
-------------------------------------------

In the ``ci/test-upgrade`` file:

* rename the current development version test (e.g. ``v210``) to the next version (``v211``) with the
  ``create`` function,
* add the migration test from the new version (``v210``) with the ``create-old`` function and the used image
  tag (e.g. ``2.10.0``), and add the associated case and cleanup.

In the ``.github/workflows/main.yaml`` file, add the ``ci/test-upgrade`` step of the new version.

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

  | x.y | To be defined |

The GHCI application uses this file to keep the Renovate ``baseBranchPatterns`` and the
``backport <version>`` labels up to date.

Create the pull request
-----------------------

.. prompt:: bash

    NEXT_VERSION=x.y+1
    git checkout -b "start-${NEXT_VERSION}"
    git add --all
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
