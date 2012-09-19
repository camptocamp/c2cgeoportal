.. _integrator_create_application:

Create a new application
========================

Creating a new c2cgeoportal application is done by applying two Paste skeletons
(a.k.a. templates and scaffolds). These skeletons are provided by the
``c2cgeoportal`` package. So to be able to create a c2cgeoportal application
the ``c2cgeoportal`` package must be installed.

If you already have a c2cgeoportal application installed, and if that
application uses a version of c2cgeoportal that fits you, then you don't need
to install c2cgeoportal again. Instead, you can use the version of c2cgeoportal
that is already alongside the existing c2cgeoportal application (in the
``buildout/eggs`` directory).

.. note::

    Some c2cgeoportal applications provide their own skeletons. For example
    a *parent* application may provide a skeleton for creating *child*
    applications. In that case, the c2cgeoportal skeletons, as well as the
    application skeletons, should be applied.

System Requirements
-------------------

To be able to create a c2cgeoportal application you need to have the following
installed on your system:

* Git. In most cases you will want to use Git as the revision control system
  for your c2cgeoportal application.
* Python 2.7 or 2.6. Python 3.x is not yet supported.

Project structure
-----------------

In the simple case the root directory of the application is the directory
created by the c2cgeoportal skeletons (the ``c2cgeoportal_create`` and
``c2cgeoportal_update`` skeletons). Projects following a parent/child
architecture may use a different structure. Here's an example of a structure
for a project composed of a main application and sub-applications::

    <root>
      ├─ <main_project>
      ├─ <first_sub_project>
      ├─ <second_sub_project>
      └─ ...

Here ``<root>`` is the root of the Git (or SVN) tree.

Install c2cgeoportal
--------------------

This step is required if you cannot, or do not want, to create the c2cgeoportal
application from an existing one. For example, if you are creating a child
application from an existing parent application then it means you already have
``c2cgeoportal`` installed, you can then just skip this section and directly go
to the next.

Also, installing ``c2cgeoportal``, as described in this section, requires
access to the c2cgeoportal GitHub repository. If you can't view the
https://github.com/camptocamp/c2cgeoportal page in your browser that means you
do not have the required permissions. Please contact Camptocamp in that case.

To install ``c2cgeoportal`` you first need to clone the c2cgeoportal repository
from GitHub::

    git clone git@github.com:camptocamp/c2cgeoportal.git
    cd c2cgeoportal
    git submodule update --init

Now run the ``bootstrap.py`` script to boostrap the Buildout environment::

    python bootstrap.py --version 1.5.2 --distribute --download-base \
        http://pypi.camptocamp.net/distribute-0.6.22_fix-issue-227/ --setup-source \
        http://pypi.camptocamp.net/distribute-0.6.22_fix-issue-227/distribute_setup.py

Install c2cgeoportal::

    ./buildout/bin/buildout

.. note::

    The above command downloads the latest *final* ``c2cgeoportal`` package from
    http://pypi.camptocamp.net/internal-pypi/index/.

    To install a development package of c2cgeoportal from
    http://pypi.camptocamp.net/internal-pypi/index/ you can edit buildout.cfg
    and set ``prefer-final`` to ``false``.

    And if you want to install a development package from the c2cgeoportal
    source you just cloned use::

        ./buildout/bin/buildout -c buildout_dev.cfg

List existing templates
-----------------------

To list the available template use the following command, from the root
directory of c2cgeoportal or an existing c2cgeoportal application::

    ./buildout/bin/pcreate -l

You should have at least the following templates:

* c2cgeoportal_create
* c2cgeoportal_update

.. note::

    With ``c2cgeoportal`` 0.6 and lower use::

        ./buildout/bin/paster create --list-templates

Create the new application
--------------------------

To simplify the rest of the procedure we set the new project name in a shell
variable::

    PROJECT=<project_name>

Replace ``<project_name>`` with a project name of your choice.
The project name can be CamelCase but lower case is recommended.

Create the application skeleton
...............................

To create the application first apply the ``c2cgeoportal_create`` skeleton::

    ./buildout/bin/pcreate -s c2cgeoportal_create ../$PROJECT

.. note::
    Don't add any '/' after the project name.

You'll be asked to enter the SRID for this project.

.. note::

   With ``c2cgeoportal`` 0.6 and lower use::

       ./buildout/bin/paster create --template=c2cgeoportal_create --output-dir=.. $PROJECT

.. note::

    If you need a specific name for the Python package defined by the project
    you can use::

        pcreate -s c2cgeoportal_create ../$PROJECT package=<package_name>


Now apply the ``c2cgeoportal_update`` skeleton::

    ./buildout/bin/pcreate -s c2cgeoportal_update ../$PROJECT

.. note::
    Don't add any '/' after the project name.

The ``c2cgeoportal_update`` scaffold is also used to update the
application. The files generated by this skeleton are prefixed with
``CONST_``, which means they are *constant* files that should not be changed.
Following this rule is important for easier updates.

.. note::

    With ``c2cgeoportal`` 0.6 and lower use::

        ./buildout/bin/paster create --template=c2cgeoportal_update --output-dir=.. $PROJECT

.. note::

   If the project provides an additional template it can be applied now::

        ./buildout/bin/pcreate --overwrite -s <project_template> ../$PROJECT


Go to your new project::

    cd ../$PROJECT


``pcreate`` doesn't conserve file permission, so restore it manually::

    chmod +x deploy/hooks/post-restore-database.in 


If this application is not part of a parent/child architecture, or is
a ``parent`` application, you can just remove the
``buildout_child.cfg`` and ``config_child.yaml.in`` files::

    rm buildout_child.cfg config_child.yaml.in

If this application is a ``child`` application make ``buildout_child.cfg`` the
main Buildout configuration file, and ``config_child.yaml.in`` the config file::

    rm buildout.cfg config.yaml.in
    mv buildout_child.cfg buildout.cfg
    mv config_child.yaml.in config.yaml.in

.. note::

    In a parent/child architecture one instance of the application is the
    parent, the others are children. Child instances display layers
    served by the parent instance. Parent and child instances share
    the same database, but use dedicated schemas within that database.

Put the application under revision control
------------------------------------------

Remove the ``egg-info`` directory, as it shouldn't be added to the
application's source repository::

    rm -rf *.egg-info

Now is a good time to put the application source code under revision
control (Git preferably).

.. note::

   We use the http URL to allow everybody to clone.

To add a new child in an existing repository
............................................

Add the project::

    cd ..
    git add $PROJECT/

Add the CGXP submodule::

    git submodule add https://github.com/camptocamp/cgxp.git $PROJECT/$PROJECT/static/lib/cgxp
    git submodule foreach git submodule update --init

Commit and push on the main repository::

    git commit -m "initial commit of $PROJECT"
    git push origin master

To add a project in a new repository
....................................

Add the project::

    git init
    git add $PROJECT/ .gitignore .httpauth \
            CONST_CHANGELOG.txt CONST_TIPS.txt.in \
            CONST_buildout.cfg buildout.cfg buildout/ \
            bootstrap.py setup.cfg setup.py \
            development.ini.in production.ini.in \
            jsbuild/ print/ apache/ \
            mapserver/ tilecache/ deploy/
    git remote add origin git@git.camptocamp.com:/srv/git/$PROJECT

Add the CGXP submodule::

    git submodule add https://github.com/camptocamp/cgxp.git $PROJECT/static/lib/cgxp
    git submodule foreach git submodule update --init

Commit and push on the main repository::

    git commit -m "initial commit"
    git push origin master

Configure the application
-------------------------

As the integrator you need to edit two files to configure the application:
``config.yaml`` and ``buildout.cfg``.

``config.yaml`` includes the *static configuration* of the application.  This
configuration is to be opposed to the *dynamic configuration*, which is in the
database, and managed by the *administrator*. The static configuration
includes for example the application's default language (specified with
``default_locale_name``).  It also includes the
configuration for specific parts of the application, like
:ref:`integrator_raster` web services.

``buildout.cfg`` includes the execution environment configuration. In this
files are set *environment variables* such as the application instance id
(``instance_id``), the database name (``db``), and host names. Pay particular
attention to the ``to_be_defined`` values. ``buildout.cfg`` actually defines
the *default* environment configuration. The configuration for specific
installations (specific servers for example) can be written in specific files,
that extend ``buildout.cfg``.  The :ref:`integrator_install_application`
section provides more information.

Don't miss to add your changes to git::

    git add buildout.cfg
    git commit -m "initialise buildout.cfg"
    git push origin master

.. note::
    If you use the check collector don't miss to add the new child to
    the parent site check_collector configuration.

.. note::
   Additional notes for Windows users:

   To have a working PNG print you should edit the file
   ``print/WEB-INF/classes/spring-application-context.xml``
   and replace the line::

        <value>/usr/bin/convert</value>

   by this one::

        <value>C:\Program Files (x86)\ImageMagick-6.7.7-Q16\convert</value>

   with the right path to ``convert``.


After creation and minimal setup the application is ready to be installed.
Then follow the sections in the install application guide:

* :ref:`integrator_install_application_create_schema`.
* :ref:`integrator_install_application_create_user`.
* :ref:`integrator_install_application_bootstrap_buildout`.
* :ref:`integrator_install_application_install_application`.

.. note::
    If you create the main instance you should do the whole
    database creation as described in :ref:`integrator_install_application`,
    except the 'Get the application source tree' chapter.


.. Minimal setup of the application
.. --------------------------------

.. This section provides the minimal set of things to do to get a working
.. application.

.. Defining background layers
.. --------------------------

.. A c2cgeoportal application has *background layers* and *overlays*. Background
.. layers, also known as base layers, sit at the bottom of the map. They're
.. typically cached layers. Overlays represent application-specific data. They're
.. displayed on top of background layers.

.. Background layers are created by the application integrator, while overlays are
.. created by the application administrator. This is why only background layers
.. are covered here in the Integrator Guide. Defining overlays is described in the
.. :ref:`administrator_guide`.

.. Create a WMTS layer (**To Be Changed**)

.. * Make sure that ``/var/sig/tilecache/`` exists and is writeable by the user ``www-data``.
.. * Add the matching layers definitions in the mapfile (``mapserver/c2cgeoportal.map.in``).
.. * Add a layer entry in ``tilecache/tilecache.cfg.in``. The ``layers`` attribute
..   must contain the list of mapserver layers defined above.
.. * Update the layers list in the ``<package>/templates/viewer.js`` template.
..   The ``layer`` parameter is the name
..   of the tilecache layer entry just added in ``tilecache/tilecache.cfg.in``.

.. **To Be Completed**
