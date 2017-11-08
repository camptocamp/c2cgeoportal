.. _integrator_multiple_databases:

Using multiple databases
========================

Configuration
-------------
In your ``vars`` file, configure any database sessions
that you want to access in your GMF instance in addition to
the default database session, as follows. For example, to add sessions
from a database ``otherdb`` and from a database ``moredb``:

.. code:: yaml

   dbsessions:
      otherdb_session:
         url: postgresql://<dbuser>:<dbpassword>@<dbhost>:<dbport>/otherdb
      moredb_session:
         url: postgresql://<dbuser>:<dbpassword>@<dbhost>:<dbport>/moredb

These additional DB sessions will be automatically initialized by GMF.

Using the additional sessions
-----------------------------
In the layers enumeration of your ``vars`` file, you can now
reference the sessions defined above. For example:

.. code:: yaml

    layers:
        enum:
            <somelayer>:
                dbsession: otherdb_session


In Python code, additional sessions as configured above can be accessed
via ``DBSessions``. For example:

.. code:: python

    from c2cgeoportal_commons.models import DBSessions
    ...
    other_session = DBSessions['otherdb_session']

This will provide you with a
`DB session object <http://docs.sqlalchemy.org/en/rel_1_0/orm/session_basics.html#getting-a-session>`_.
The session name for the default database is ``dbsession``.

To access attributes of your settings, proceed as follows
(example for the ``otherdb_session`` described above):

.. code:: python

    settings['dbsessions']['otherdb_session']['url']


Restrictions in multiple database usage
---------------------------------------

In a GMF instance, an editable layer can only be included when that layer's data
resides in the default database of the GMF instance.
Regarding editable layers, see :ref:`here <administrator_editing_editable>`.
The reason for this restriction is that the administrator settings currently
do not allow to specify a database session in the layer settings. Because for editable
layers, GMF always uses the configuration provided in the administration settings,
only the default database session can be used for such layers.
