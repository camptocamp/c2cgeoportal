.. _developer_development_procedure:

Development procedure
=====================

Process
-------

Any change to c2cgeoportal and CGXP requires a GitHub pull request.

To give everyone a chance to review changes pull requests should not stay open
for at least 24 hours.

Any main developers of c2cgeoportal projects can take responsibility for
merging commits in the main (``master``) branch.

Pull requests with significant impacts can and should be reviewed by more than
one person.

Working with Git and GitHub
---------------------------

Create a topic branch
~~~~~~~~~~~~~~~~~~~~~

To create a Git branch from the master branch use:

.. prompt:: bash

    git checkout -b <branch_name> master

You can then add commits to your branch, and push commits to a remote branch
using:

.. prompt:: bash

    git push -u origin <branch_name>

The ``-u`` option adds an upstream (tracking) reference for the branch. This is
optional, but convenient. Once the branch has an upstream reference you can
push commits by just using ``git push``.

The "origin" remote can either represent the main repository (that in the
"camptocamp" organization) or your own fork. Creating branches in the main
repository can ease collaboration between developers, but isn't required.

Sync up a topic branch from master
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To update a branch from the master you first need to update your
local master branch:

.. prompt:: bash

    git checkout master
    git fetch origin
    git merge origin/master

.. note::

    You'll use "upstream" instead of "origin" if "origin" references
    your own fork.

You can now update your branch from master:

.. prompt:: bash

    git checkout <branch_name>
    git rebase master
    git push origin <branch_name>

Pull requests
~~~~~~~~~~~~~

Making a pull request is done via the GitHub web interface. Open your branch in
the browser (e.g. https://github.com/camptocamp/c2cgeoportal/tree/make) and
press the ``Pull Request`` button.

Once a pull request is merged it is good practise to add a comment in the pull
request, for others to get notifications.

Remove branches
~~~~~~~~~~~~~~~

Once you are done with a topic branch (because its commits are merged
in the master branch) you can remove it with:

.. prompt:: bash

    git branch -D <branch_name>

To remove a remote branch use:

.. prompt:: bash

    git push origin :<branch_name>

This means push nothing to "branch_name" on the origin remote.
