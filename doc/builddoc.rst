.. _build_doc:

Build this doc
==============

.. prompt:: bash

  ./docker-run make doc

The HTML should now be available in the ``doc/_build/html`` directory.

Contribute to the documentation
-------------------------------

You can contribute to the documentation by making changes to the git-managed
files and creating a pull request, just like for any change proposals to
c2cgeoportal or other git managed projects.

To make changes to the documentation, you need to edit the ``.rst.mako``
files where available; otherwise directly the ``.rst`` if there is no corresponding
``mako`` file.

To verify that the syntax of your changes is OK (no trailing whitespace etc.),
you should execute the following command (in addition to the ``make doc``):

.. prompt:: bash

  ./docker-run make git-attributes
