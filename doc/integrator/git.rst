.. _administrator_deploy:

Quick introduction to Git
=========================

Overview
--------

Git is a `revision control <http://en.wikipedia.org/wiki/Revision_control>`_ 
like Subversion but he is 
`distributed <http://en.wikipedia.org/wiki/Distributed_revision_control>`_.

The following lines will not demonstrate the power of GIT but the 
minimal commands to know to use it the same as a Subversion repository.

.. attention::
   the following command consider that we work directly on the master
   branch, than it shouldn't be used to work on the frameworks
   because we use branches.


Get the code
------------

The Git commands to the code from a remote repository is named ``clone``::

    git clone <url_to_the_remote_repository> <local_folder>

Than we need also download the dependencies named as ``submodule``
(two level in our case)::

    git submodule update --init
    git submodule foreach git submodule update --init

Update the code
---------------

When we want to gets the changes from other people who is working on
the project we need to ``pull`` the new code::

    git pull

And if the submodules where updated::

    git submodule sync
    git submodule update
    git submodule foreach git submodule sync
    git submodule foreach git submodule update

Send your modification
----------------------

To send your modification you should do tree steps, the first 
is to ``add`` your files to the ``index``::

    git add <files>

The second is to ``commit`` the ``index`` to locale repository::

    git commit -m "<message_that_describe_your_changes>"

And the third is to send your changes to the remote repository::

    git push


That's all :-).

