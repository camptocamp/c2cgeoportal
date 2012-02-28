.. _administrator_deploy:

Quick introduction to Git
=========================

Overview
--------

Git is a `revision control system <http://en.wikipedia.org/wiki/Revision_control>`_ 
like Subversion but it is 
`distributed <http://en.wikipedia.org/wiki/Distributed_revision_control>`_.

The following lines will not demonstrate the power of Git but the 
minimal commands to use as a Subversion repository.

.. attention::
   the following command consider that we work directly on the master
   branch, than it shouldn't be used to work on the frameworks
   because we use branches.

Here we just specify the commands used to send your modifications,
for other commands they will be directly in the documentation.

Send your modification
----------------------

Three steps are required to send a modification. The first one
is to ``add`` your files to the ``index``::

    git add <files>

The second one is to ``commit`` the ``index`` to local repository::

    git commit -m "<message_that_describe_your_changes>"

And the third one is to send your changes to the remote repository::

    git push

