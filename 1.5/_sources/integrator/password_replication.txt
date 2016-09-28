.. _integrator_password_replication:

Password Replication
====================

*New in c2cgeoportal 1.4*

To replicate a password change between the main database and a secondary 
database, you need to add the following configuration in the buildout 
configuration file used to setup your project::

    # enable / disable the replication
    enable_auth_replication = true

    # the target database connection configuration
    dbhost_replication: <target database hostname>
    dbport_replication: <target database port>
    db_replication: <target database name>
    dbuser_replication: <target database username>
    dbpassword_replication: <target database password>

The target database is the secondary database where the changes are being 
replicated.

Also be sure you have the following line in your development.ini.in / 
production.ini.in in the [app:app] section::

    auth_replication_enabled = ${vars:enable_auth_replication}
    sqlalchemy_replication.url = postgresql://${dbuser_replication}:${dbpassword_replication}@${dbhost_replication}:${dbport_replication}/${db_replication}
