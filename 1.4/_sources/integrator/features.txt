.. _integrator_features:

Additional features
===================

This section describes how to add features to a c2cgeoportal project,
and configure them.

Adding a feature requires adding a *plugin*  (CGXP plugin) to the user
interface's *viewer*. It may also require additional steps, like adding and
populating tables in the database.

A c2cgeoportal project may define multiple viewers. By default a project
includes two viewers: the *main viewer* and the *editing viewer*. The main
viewer is defined in the ``<package>/templates/viewer.js`` file, while the
editing viewer is defined in the ``<package>/templates/edit.js`` file. Each
viewer includes a number of plugins by default; adding/removing features
involve adding/removing plugins to/from the viewer.

See http://docs.camptocamp.net/cgxp/ for the list of available CGXP plugins.

Features that require additional steps (most of the time):

.. toctree::
   :maxdepth: 1

   fulltext_search
   querier
   editing
   print
   https
   api
   password_replication
   shortener
   intranet
   security
