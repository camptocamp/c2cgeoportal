.. _integrator_password_replication:

Password Replication
====================

To replicate a password change between the main database and a secondary 
database, you need to add the following configuration in the vars 
configuration file used to setup your project:
    
.. code:: yaml

    # enable / disable the replication
    enable_auth_replication: true

    # the target database connection configuration
    dbhost_replication: <target database hostname>
    dbport_replication: <target database port>
    db_replication: <target database name>
    dbuser_replication: <target database username>
    dbpassword_replication: <target database password>

The target database is the secondary database where the changes are being 
replicated.
