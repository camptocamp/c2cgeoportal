.. _integrator_install_application:

Install an existing application
===============================

On this page we explain all the procedures to build an application from
only the code.

For example If you want to use an existing database you should ignore
all the commands concerning the database.

This guide considers that:
 - We use a server manages by Camptocamp, meaning:
    - all dependencies described in the
      :ref:`system requirements <integrator_install_application_system_requirement>`
      section are installed
    - Postgres has a gis template 'template_postgis' and a user 'www-data'
    - Apache use the user 'www-data'
 - We use Git as revision control
 - We use a version of ``c2cgeoportal`` >= 0.7

For the others system there is some notes to give some help.

.. _integrator_install_application_system_requirement:

System requirements
-------------------

To install a c2cgeoportal application you need to have the following installed
on your system:

* Git (or whatever revision control (for example Subversion)
    is used for the application)
* Python 2.6, 2.7 (2.5 or 3.x are not supported)
* Oracle Java SE Development Kit 6 or 7
* Tomcat
* Apache
* PostgreSQL >= 9.1/PostGIS 1.5.3 (PostgreSQL 8.x and 9.0 should work but some adaptations
    are required)
* MapServer 6.0.x (MapServer 6.0.0 and 6.0.1 have some issue in WFS, not all versions 
    >= 6.2 are compatible)
* ImageMagick

.. note::
    Additional notes for Windows users:

        For Subversion install `Tortoises SVN <http://tortoisesvn.net>`_.

        For Git look at GitHub's `Set Up Git page
        <http://help.github.com/win-set-up-git/>`_. You won't need to set up SSH
        keys, so you only need to follow the first section of this page.

        Once Git is installed use Git Bash for all the shell commands provided in
        this documentation. You'll need to make sure the Turtoise, Python, and Java
        folders are defined in your system ``PATH``. For example if you have Python installed under
        ``C:\Python26`` you can use ``export PATH=$PATH:/c/Python26`` to add Python
        to your ``PATH``.

        You need to install the ``psycopg2`` Python package in the main Python
        environment (e.g. ``C:\Python26``). Use an installer (``.exe``) from the
        `Stickpeople Project
        <http://www.stickpeople.com/projects/python/win-psycopg/>`_.

        When you download and configure Apache be sure that modules ``header_module``,
        ``expire_module`` and ``rewrite_module`` are uncommented. You must also download
        and add modules ``mod_wsgi`` (http://modwsgi.readthedocs.org/) and ``mod_fcgid``
        (https://httpd.apache.org/mod_fcgid/).

Set up the database
-------------------

Any c2cgeoportal application requires a PostgreSQL/PostGIS database. The
application works with its own tables, which store users, layers, etc. These
tables are located in a specific schema of the database.

.. note::

    Multiple specific schemas are actually used in a parent/child architecture.

If the application has MapServer layers linked to PostGIS tables, these tables
and the application-specific tables must be in the same database, preferably in
separate schemas. This is required for layer access control (*restricted
layers*), where joining user/role tables to PostGIS layer tables is necessary.

Create the database
~~~~~~~~~~~~~~~~~~~

To create the database you can use::

    $ sudo -u postgres createdb <db_name> -T template_postgis

with ``<db_name>`` replaced by the actual database name.

.. note::

   if you don't have the template_postgis you can use::

       sudo -u postgres createdb -E UTF8 -T template0 <db_name>
       sudo -u postgres psql -d <db_name> -f /usr/share/postgresql/9.1/contrib/postgis-1.5/postgis.sql
       sudo -u postgres psql -d <db_name> -f /usr/share/postgresql/9.1/contrib/postgis-1.5/spatial_ref_sys.sql

   Note that the path of the postgis scripts and the template name can
   differ on your host.

.. _integrator_install_application_create_schema:

Create the schema
~~~~~~~~~~~~~~~~~

Each parent or child needs two application-specific schemas,
then to create it use::

    sudo -u postgres psql -c "CREATE SCHEMA <schema_name>;" <db_name>
    sudo -u postgres psql -c "CREATE SCHEMA <schema_name>_static;" <db_name>

with ``<db_name>`` and ``<schema_name>`` replaced by the actual database name,
and schema name ('main' by default), respectively.

.. _integrator_install_application_create_user:

Create a database user
~~~~~~~~~~~~~~~~~~~~~~

We use a specific user for the application, ``www-data`` by default.

.. note::

   It the user doesn't already exist in your database, create it first::

        sudo -u postgres createuser -P <db_user>
        sudo -u postgres psql -c 'GRANT SELECT ON TABLE spatial_ref_sys TO <db_user>' <db_name>
        sudo -u postgres psql -c 'GRANT ALL ON TABLE geometry_columns TO <db_user>' <db_name>

Give the rights to the user::

    sudo -u postgres psql -c 'GRANT ALL ON SCHEMA <schema_name> TO "www-data"' <db_name>
    sudo -u postgres psql -c 'GRANT ALL ON SCHEMA <schema_name>_static TO "www-data"' <db_name>

.. note::

   If you don't use the www-data user for Apache replace it by the right user.


Install the application
-----------------------

Get the application source tree
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If Git is used for the application use the following command to get the
application source tree::

    git clone git@github.com:camptocamp/<my_project>.git <my_project>

c2cgeoportal applications include a Git submodule for CGXP. The following
commands should be used to download CGXP and its dependencies::

    cd <my_project>
    git submodule update --init
    git submodule foreach git submodule update --init

The ``foreach`` command aims to init and update CGXP's own submodules, for GXP,
OpenLayers and GeoExt.

.. note::

    We don't just use ``git submodule update --init --recursive`` here because
    that would also download GXP's submodules. We don't want that because we
    don't need GXP's submodules. CGXP indeed has its own submodules for
    OpenLayers and GeoExt.

.. important::

    If you want other people than you to be able to run ``buildout`` from an
    application clone created by you then you need to change the application
    directory's permissions using ``chmod -R g+w``.  You certainly want to do
    that if the application has been cloned in a shared directory like
    ``/var/www/<vhost>/private``.

.. note::

    If you still use SVN::

        svn co https://project.camptocamp.com/svn/<my_project>/trunk <my_project>

Windows Specific Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Some changes in the apache wsgi and mapserver configurations are required to make
c2cgeoportal work on Windows.

apache/wsgi.conf.in
^^^^^^^^^^^^^^^^^^^

WSGIDaemonProcess and WSGIProcessGroup are not supported on windows.

(`WSGIDaemonProcess ConfigurationDirective
<http://code.google.com/p/modwsgi/wiki/ConfigurationDirectives#WSGIDaemonProcess>`_
"Note that the WSGIDaemonProcess directive and corresponding features are not
available on Windows or when running Apache 1.3.")

The following lines must be commented/removed::

    WSGIDaemonProcess c2cgeoportal:${vars:instanceid} display-name=%{GROUP} user=${vars:modwsgi_user}
    ...
    WSGIProcessGroup c2cgeoportal:${vars:instanceid}

apache/mapserver.conf.in
^^^^^^^^^^^^^^^^^^^^^^^^

The path to Mapserver executable must be modified::

    ScriptAlias /${vars:instanceid}/mapserv C:/path/to/ms4w/Apache/cgi-bin/mapserv.exe

.. _integrator_install_application_bootstrap_buildout:

CONST_buildout.cfg
^^^^^^^^^^^^^^^^^^

Some outputs paths must be modified for the print::

    basedir = print\
    ...
    output = C:\path\to\tomcat\webapps\print-c2cgeoportal-${vars:instanceid}.war

buildout.cfg
^^^^^^^^^^^^

It may be better to create a specific buildout file for Windows (for
instance ``buildout_windows.cfg``) that extends the buildout.cfg file.

    #. Under ``[buildout]`` add ``exec-sitecustomize = true`` to use our eggs.

    #. Under ``[template]`` add ``extends -= facts`` to ignore facts that are specific to Unix.
    
    #. Under ``[version]`` add these two lines to pick the installed version (It may be
        preferable to specify the version that you've installed):

        * ``distribute =``
        * ``psycopg2 =``

    #. Under ``[print-war]`` add ``mod = create`` because update seems not to work on Windows.


mapserver/c2cgeoportal.map.in
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You must specify the path to the mapserver's epsg file by uncommenting and adapting
this line under ``MAP`` (use regular slash ``/``) ::

    PROJ_LIB" "C:/PATH/TO/ms4w/proj/nad"


RHEL 6 Specific Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Specific settings are required when the c2cgeoportal application is to be run
on RedHat Enterprise Linux (RHEL) 6.

.. note::

    First of all, note that, with RHEL, you cannot install the c2cgeoportal
    application in your homedir. If you do so, you will get the following error
    in the Apache logs::

        (13)Permission denied: access to /~elemoine/ denied

    So always install the application in an Apache-accessible directory. On
    Camptocamp *puppetized* servers you will typically install the application
    in ``/var/www/vhosts/<vhost>/private/dev/<username>/``, where ``<vhost>``
    is the name of the Apache virtual host, and ``<username>`` is your Unix
    login name.

buildout.cfg
^^^^^^^^^^^^

By default, ``mod_wsgi`` processes are executed under the ``www-data`` Unix
user, which is the Apache user. In RHEL 6, there's no user ``www-data``, and
the Apache user is ``apache``. To accomodate that edit ``buildout.cfg`` and
set ``modwsgi_user`` to ``apache`` in the ``[vars]`` section::

    [vars]
    ...
    modwsgi_user = apache


Also, by default, the path to Tomcat's ``webapps`` directory is
``/srv/tomcat/tomcat1/webapps``. On RHEL 6, Tomcat is located in
``/var/lib/tomcat6/``. To accomodate that the ``output`` path of the
``[print-war]`` part should be changed::

    [print-war]
    output = /var/lib/tomcat6/webapps/print-c2cgeoportal-${vars:instanceid}.war

apache/mapserver.conf.in
^^^^^^^^^^^^^^^^^^^^^^^^

On RHEL 6 the ``mapserv`` binary is located in ``/usr/libexec/``. The
``mapserver.conf.in`` Apache config file assumes that ``mapserv`` is located in
``/usr/lib/cgi-bin/``, and should therefore be changed::

    ScriptAlias /${vars:instanceid}/mapserv /usr/libexec/mapserv

apache2ctl
~~~~~~~~~~

On RedHat the commands hasn't the '2'!
Then to graceful apache do::

    /usr/sbin/apachectl graceful

Buildout bootstrap
~~~~~~~~~~~~~~~~~~

The `Buildout <http://pypi.python.org/pypi/zc.buildout/1.5.2>`_ tool is used to
build, install, and deploy c2cgeoportal applications.

Prior to using Buildout, its ``bootstrap.py`` script should be run at the root
of the application::

  $ python bootstrap.py --version 1.5.2 --distribute --download-base \
        http://pypi.camptocamp.net/distribute-0.6.22_fix-issue-227/ --setup-source \
        http://pypi.camptocamp.net/distribute-0.6.22_fix-issue-227/distribute_setup.py

This step is done only once for installation/instance of the application.

.. Note::

    If you have permissions issues on Windows you can try to set the TMP
    path variable to a folder that you created (like ``C:\tmp``). If
    the problem persists don't use the proxy by using this command instead
    (where buildout_windows.cfg is your specific buildout for Windows
    as configured above)::

        $ python bootstrap.py --version 1.5.2 --distribute -c buildout_windows.cfg

.. _integrator_install_application_install_application:

Install the application
~~~~~~~~~~~~~~~~~~~~~~~

If it doesn't already exist, create a ``buildout_<user>.cfg`` file
(where ``<user>`` is for example your username),
that will contain your application special
configuration::

    [buildout]
    extends = buildout.cfg
    parts -= fix-perm

    [vars]
    instanceid = <instanceid>

    [jsbuild]
    compress = False

    [jsbuild-mobile]
    compress = False

    [cssbuild]
    compress = false

.. note::

    The ``<instanceid>`` should be unique on the server, the username is a good
    choice or something like ``<user>-<sub-project>`` in case of parent/children project.

    ``parts -= fix-perm`` disables the ``fix-perm`` task that may take some
    time whereas it is not needed in a personal environment.

Add it to Git::

    git add buildout_<user>.cfg
    git commit -m "add user buildout"

.. note::
    for SVN users::

        svn add buildout_<user>.cfg
        svn commit -m "add user buildout"

Then you can build and install the application with the command::

    ./buildout/bin/buildout -c buildout_<user>.cfg

This previous command will do many things like:

  * download and install the project dependencies,

  * adapt the application configuration to your environment,

  * build the javascript and css resources into compressed files,

  * compile the translation files.

Once the application is built and installed, you now have to create and
populate the application tables, and directly set the version (details later)::

    $ ./buildout/bin/create_db --populate
    $ ./buildout/bin/manage_db version_control `./buildout/bin/manage_db version`

.. note::

    With c2cgeoportal 0.7 and lower, or if the app section is not ``[app:app]``
    in the production.ini file, you need to specify the app name on the
    ``manage_db`` command line. For example, the above command would be as
    follows::

        $ ./buildout/bin/manage_db -n <package_name> version_control \
          `./buildout/bin/manage_db -n <package_name> version`

A c2cgeoportal application makes use of ``sqlalchemy-migrate`` to version
control a database. It relies on a **repository** in source code which contains
upgrade scripts that are used to keep the database up to date with the
latest repository version.

After having created the application tables with the previous command,
the current database version correspond to the latest version available in
the repository, which can be obtained with::

    $ ./buildout/bin/manage_db version
    <current_version>
    $

Note that future schema upgrades will only be done via change scripts from the
repository, and they will automatically increment the ``db_version``.

Your application is now fully set up and the last thing to do is to configure
apache so that it will serve your WSGI c2cgeoportal application. So you just
have to include the application apache configuration available in the
``apache`` directory. On servers managed by Camptocamp, add a ``.conf`` file in
``/var/www[/vhost]/<vhostname>/conf/`` (``[/vhost]`` means that the vhost folder
is optional, ``<vhostname>`` is a folder that should already exist (created by
the system administrator), that corresponds to the virtual host)
with the following content::

    Include /<project_path>/apache/*.conf

where ``<project_path>`` is the path to your project.

Reload apache configuration and you're done::

    $ sudo /usr/sbin/apache2ctl graceful

Your application should be available at:
``http://<hostname>/<instanceid>/wsgi``.

Where the ``<hostname>`` is directly linked to the virtual host,
and the ``<instanceid>`` is the value you provided before.
