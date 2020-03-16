.. _integrator_create_application:

Create a new application
========================

Creating a new c2cgeoportal application is done by applying two Paste scaffolds
(a.k.a. templates and scaffolds). These scaffolds are provided by the
``c2cgeoportal`` package. Therefore, to be able to create a c2cgeoportal application,
the ``c2cgeoportal`` package must be installed.

If you already have a c2cgeoportal application installed, and if that
application uses a version of c2cgeoportal that fits you, then you do not need
to install c2cgeoportal again. Instead, you can use the version of c2cgeoportal
that is already alongside the existing c2cgeoportal application.

.. note::

    Some c2cgeoportal applications provide their own scaffolds. For example in a
    multi-project application, a *parent* application may provide a scaffold for
    creating *child* applications. In that case, the c2cgeoportal scaffolds, as
    well as the application scaffolds, should be applied.

Project structure
-----------------

In the simple case, the root directory of the application is the directory
created by the c2cgeoportal scaffolds (the ``c2cgeoportal_create`` and
``c2cgeoportal_update`` scaffolds).

Install c2cgeoportal
--------------------

To get ``c2cgeoportal``, you need to get the related docker image and the
``docker-run`` script:

.. prompt:: bash

   docker pull camptocamp/geomapfish-build:<release|version>
   wget https://raw.githubusercontent.com/camptocamp/c2cgeoportal/<version>/docker-run
   chmod +x docker-run

.. note::

   If you are behind a proxy, you may pass proxy connection information to the ``docker`` command,
   respectively to the ``docker-run`` script, with ``--env`` parameters, like this:

   .. code:: bash

       --env http_proxy=...

List existing scaffolds
-----------------------

To list the available scaffolds, use the following command, either
from the root directory of c2cgeoportal (if you have followed the instructions
from the previous section), or from the root directory of the existing
c2cgeoportal application you want to create the new application from:

.. prompt:: bash

    ./docker-run --image=camptocamp/geomapfish-build ${'\\'}
        --version=<release|version> pcreate -l

You should at least see the c2cgeoportal scaffolds:

* c2cgeoportal_create
* c2cgeoportal_nondockercreate
* c2cgeoportal_nondockerupdate
* c2cgeoportal_update

Create the new application
--------------------------

The first step in the project creation is to choose a project name
``<project>``, and a package name ``<package>``.

Normally, the project name should be the same name as the Git repository name.

The package name should not contain any underscores (``_``), because of an
issue with Pip.

To create the application, first apply the ``c2cgeoportal_create`` scaffold:

.. prompt:: bash

   ./docker-run -ti --image=camptocamp/geomapfish-build ${'\\'}
       --version=<release|version> ${'\\'}
       pcreate -s c2cgeoportal_create --package-name <package> <project>

If you want to use the non Docker runtime, apply also the
``c2cgeoportal_nondockercreate`` scaffold:

.. prompt:: bash

   ./docker-run -ti --image=camptocamp/geomapfish-build ${'\\'}
       --version=<release|version> ${'\\'}
       pcreate -s c2cgeoportal_nondockercreate <project>

.. note::

    Do not add any '/' after the project name.

You will be asked to enter the SRID and the Apache vhost for this project. Note
that the default extent would be defined directly from the SRID. You can change
it later.

.. note::

    You can define this information directly in the command line using
    parameters:

     .. prompt:: bash

        ./docker-run -ti --image=camptocamp/geomapfish-build ${'\\'}
            --version=<release|version> ${'\\'}
            --env=SRID=21781 --env=EXTENT="420000,30000,900000,350000" ${'\\'}
            pcreate -s c2cgeoportal_create --package-name <package> <project>

This will create a directory named ``<project>`` that will be next to the
``c2cgeoportal`` directory, or to the directory of the application you are
creating this application from.

Now apply the ``c2cgeoportal_update`` scaffold:

.. prompt:: bash

   ./docker-run -ti --env=SRID=21781 ${'\\'}
       --image=camptocamp/geomapfish-build --version=<release|version> ${'\\'}
       pcreate -s c2cgeoportal_update --package-name <package> <project>

And for the non Docker version, apply also the ``c2cgeoportal_nondockerupdate`` scaffold:

.. prompt:: bash

   ./docker-run -ti --env=SRID=21781 ${'\\'}
       --image=camptocamp/geomapfish-build --version=<release|version> ${'\\'}
       pcreate -s c2cgeoportal_nondockerupdate --package-name <package> <project>


.. note::

    Do not add any '/' after the project name.

The ``c2cgeoportal_update`` scaffold is also used to update the
application. The files generated by this scaffold are prefixed with
``CONST_``, which means they are *constant* files that should not be changed.
Following this rule is important for easier updates.


Go to your new project:

.. prompt:: bash

    cd <project>


Put the application under revision control
------------------------------------------

Now is a good time to put the application source code under revision
control wth Git.

To add a project in a new repository
....................................

Add the project:

.. prompt:: bash

    git init
    git add .
    git remote add origin git@github.com:camptocamp/<project>.git

Commit and push on the main repository:

.. prompt:: bash

    git commit -m "Initial commit"
    git push origin master

Configuration of different environments in your project
-------------------------------------------------------

Concepts
........

* Makefile: These files are environment configuration files. Each environment will
  have its configuration file (for example: developer, preprod, prod)
* vars_xxx.yaml: These files are application configuration files. Generally only
  one file is needed to configure your application.

Hierarchy and extending your configuration files
................................................

The configuration files (Makefile and vars) are organized in a hierarchy.
A Makefile extends another Makefile and similarly a vars file extends another vars file.
This extension mechanism is used in Makefile files as follows:

.. code:: make

   include CONST_Makefile

and in vars files as follows:

.. code:: yaml

    extends: CONST_vars.yaml

``CONST`` files are files that should not be changed, because they are replaced
during application updates, so your changes will be systematically lost. You can
extend these files as many times as you like, although it is not recommended to
exceed 3-4 levels for readability and simplicity.

.. image:: ../_static/doc_hierarchie.png

Whenever possible, it is strongly advised not to extend the ``vars.yaml`` file.
We recommend instead that you use dynamic variables as described below.
However, in some use cases extending ``vars.yaml`` may be needed:

* Configuring highly specific environments
* Configuration of a multi-project

Use of dynamic variables
........................

Variables used in the application configuration files (files ``vars.yaml``)
can be made dynamic by means of environment variables. For this, in the main file
``vars.yaml``, add a block ``interpreted`` at the bottom of the file.

In this same file, you can change the value of a parameter by putting it in
uppercase (example: ``host: HOST``). This parameter must be listed in the
interpreted parameters section:

.. code:: yaml

    extends: CONST_vars.yaml

    vars:
        host: HOST
    ...
    interpreted:
        environment:
            - log_level
            - host

In the ``Makefile`` file, add parameters you want to change as exported variables:

.. code:: make

    export HOST = domaine.different.com
    export LOG_LEVEL

In the Makefiles that extend this main file, you only need to define the
environment variables:

.. code:: make

   export HOST = prod.different.com

Configure the application
-------------------------

As the integrator, you need to edit the ``vars.yaml`` and ``Makefile`` files to configure the application.

Do not forget to add your changes to git:

.. prompt:: bash

    git add vars.yaml
    git commit -m "Configure the project"
    git push origin master

.. note::

    If you are using a multi-project, you should add all new children to
    the parent site check_collector configuration.

.. note::

   Additional notes for Windows users:

   To have a working PNG print, you should get and edit the file
   ``print/WEB-INF/classes/imagemagick-mapfish-spring-application-context-override.xml``,
   get it:

   .. prompt:: bash

        wget https://raw.github.com/mapfish/mapfish-print/master/sample-spring/imagemagick/WEB-INF/classes/imagemagick-mapfish-spring-application-context-override.xml
        mv imagemagick-mapfish-spring-application-context-override.xml print/WEB-INF/classes/
        git add print/WEB-INF/classes/imagemagick-mapfish-spring-application-context-override.xml

   and replace the lines::

        <!-- <property name="cmd">
            <value>C:\Program Files\ImageMagick-6.7.8-Q16\convert</value>
        </property> -->

   by those ones::

        <property name="cmd">
            <value>C:\Program Files\ImageMagick-6.7.8-Q16\convert</value>
        </property>

   with the right path to ``convert``.

Now, the application is ready to be installed.
Follow the sections in the install application guide:

* :ref:`integrator_install_application_setup_database`.
* :ref:`integrator_install_application_create_schema`.
* :ref:`integrator_install_application_install_application`.

.. note::

   If you want a default theme, you can run:

   .. prompt:: bash

      ./docker-compose-run create-demo-theme

.. note::

    If you create the main instance, you should do the whole
    database creation as described in :ref:`integrator_install_application`,
    except the 'Get the application source tree' chapter.


Dynamic configuration and autogenerated files
---------------------------------------------

Several files are autogenerated, their content depending of the variables you
have set either in the main ``<package>.mk`` or a ``<user>.mk``

The files can have the extension ``.mako``

.mako
.....

If you use ``.mako``, you can also use all the possibilities allowed by the Mako
templating system, such as for loops, conditions, sub-templates, etc.

Please see the Mako documentation for details:

https://docs.makotemplates.org/en/latest/

The result of the templating is a file without the ``.mako`` extension.

**Syntax**

In ``.mako`` files, the variable replacement syntax is as follows:

.. code:: mako

  ${'$'}{<variablename>}

For example:

.. code:: mako

  ${'$'}{directory}
