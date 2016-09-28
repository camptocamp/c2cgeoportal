.. _developer_transiflex:

Transifex
=========

We use Transifex to localise the server part (essentially the admin interface).

`c2cgeoportal Transifex interface <https://www.transifex.com/projects/p/geomapfish/resource/c2cgeoportal/>`_.

To access the Transifex service and synchronize the localisation files
you must create a `~/.transifexrc` config file:

.. code::

   [https://www.transifex.com]
   hostname = https://www.transifex.com
   username = <username>
   password = <password>
   token =

And run the command:

.. prompt:: bash

   make transifex-sync

It will push the current pot file and get the French and German po files.
