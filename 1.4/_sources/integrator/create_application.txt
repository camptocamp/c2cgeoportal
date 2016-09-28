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

Requirements
------------

To be able to create a c2cgeoportal application you need to have the following
installed on your system:

* Git. In most cases you will want to use Git as the revision control system
  for your c2cgeoportal application.
* Python 2.7. Python 3.x is not yet supported.

Project structure
-----------------

In the simple case the root directory of the application is the directory
created by the c2cgeoportal skeletons (the ``c2cgeoportal_create`` and
``c2cgeoportal_update`` skeletons). Projects following a parent/child
architecture may use a different structure. Here's an example of a structure
for a project composed of a main application and sub-applications::

    <root>
      +- <main_project>
      +- <first_sub_project>
      +- <second_sub_project>
      +- ...

Here ``<root>`` is the root of the Git (or SVN) tree.

Install c2cgeoportal
--------------------

This step is required if you cannot, or do not want, to create the c2cgeoportal
application from an existing one. For example, if you are creating a child
application from an existing parent application, it means you already have
``c2cgeoportal`` installed, so you can just skip this section, and directly go
to the next.

Also, installing ``c2cgeoportal``, as described in this section, requires
access to the c2cgeoportal GitHub repository. If you can't view the
https://github.com/camptocamp/c2cgeoportal page in your browser that means you
do not have the required permissions. Please contact Camptocamp in that case.

To install ``c2cgeoportal`` you first need to clone the c2cgeoportal repository
from GitHub::

    git clone https://github.com/camptocamp/c2cgeoportal.git
    cd c2cgeoportal

Then you should checkout the branch or tag of the version you want to install::

    git checkout <branch|tag>
    git submodule update --init

``<branch|tag>`` can be ``1.4`` for the latest version of the 1.4 branch,
``1.4.0`` for the first stable 1.4 version.

.. note::

    To install c2cgeoportal version ``1.3`` and previous you should get the
    branch ``1.3``::

        git checkout 1.3
        git submodule update --init

    To install a release candidate or a specific development version you
    should add in the section ``[versions]`` of ``buildout.cfg`` the version
    of c2cgeoportal you want to install, eg. ``c2cgeoportal = 1.3rc2``.

Now run the ``bootstrap.py`` script to boostrap the Buildout environment::

    python bootstrap.py --version 1.5.2 --distribute --download-base \
        http://pypi.camptocamp.net/distribute-0.6.22_fix-issue-227/ --setup-source \
        http://pypi.camptocamp.net/distribute-0.6.22_fix-issue-227/distribute_setup.py

Build c2cgeoportal::

    ./buildout/bin/buildout

List existing skeletons
-----------------------

To list the available skeletons/templates use the following command, either
from the root directory of c2cgeoportal (if you've followed the instructions
from the previous section), or from the root directory of the existing
c2cgeoportal application you want to create the new application from::

    ./buildout/bin/pcreate -l

.. note::

    With ``c2cgeoportal`` 0.6 and lower use::

        ./buildout/bin/paster create --list-templates

You should at least see the c2cgeoportal skeletons:

* c2cgeoportal_create
* c2cgeoportal_update

Create the new application
--------------------------

To simplify the rest of the procedure we set the new project name in a shell
variable::

    PROJECT=<project_name>

Replace ``<project_name>`` with a project name of your choice.
The project name can be CamelCase but lower case is recommended.

To create the application first apply the ``c2cgeoportal_create`` skeleton::

    ./buildout/bin/pcreate -s c2cgeoportal_create ../$PROJECT

.. note::
    Don't add any '/' after the project name.

.. note::

   With ``c2cgeoportal`` 0.6 and lower use::

       ./buildout/bin/paster create --template=c2cgeoportal_create --output-dir=.. $PROJECT

.. note::

    If you need a specific name for the Python package defined by the project
    you can use::

        pcreate -s c2cgeoportal_create ../$PROJECT package=<package_name>

You'll be asked to enter the SRID for this project.

This will create a directory named ``<project_name>`` that will be next to the
``c2cgeoportal`` directory, or to the directory of the application you're
creating this application from.

Now apply the ``c2cgeoportal_update`` skeleton::

    ./buildout/bin/pcreate -s c2cgeoportal_update ../$PROJECT

.. note::
    Don't add any '/' after the project name.

.. note::

    With ``c2cgeoportal`` 0.6 and lower use::

        ./buildout/bin/paster create --template=c2cgeoportal_update --output-dir=.. $PROJECT

.. note::

   If the project provides an additional template it can be applied now::

        ./buildout/bin/pcreate --overwrite -s <project_template> ../$PROJECT

The ``c2cgeoportal_update`` scaffold is also used to update the
application. The files generated by this skeleton are prefixed with
``CONST_``, which means they are *constant* files that should not be changed.
Following this rule is important for easier updates.


Go to your new project::

    cd ../$PROJECT


``pcreate`` doesn't conserve file permission, so restore it manually::

    chmod +x deploy/hooks/post-restore-database.in

In ``versions.cfg`` make sure that c2cgeoportal version is set::

    c2cgeoportal = <version>

With ``<version>`` the egg version you want to use, normally it should be the same
number as the ``tag`` you use to checkout ``c2cgeoportal``.

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

    git submodule add https://github.com/camptocamp/cgxp.git $PROJECT/$PROJECT/static/lib/cgxp -b <version>
    git submodule foreach git submodule update --init

``-b <version>`` forces to use the CGXP branch ``<version>``.
Branches are available starting at version ``1.3``.

Commit and push on the main repository::

    git commit -m "initial commit of $PROJECT"
    git push origin master

To add a project in a new repository
....................................

Add the project::

    git init
    git add $PROJECT/ .gitignore config.yaml.in \
            versions.cfg README.rst CONST_CHANGELOG.txt \
            CONST_buildout.cfg buildout.cfg buildout/ \
            bootstrap.py setup.cfg setup.py \
            development.ini.in production.ini.in \
            jsbuild/ print/ apache/ \
            mapserver/ deploy/
    git remote add origin git@github.com:camptocamp/$PROJECT.git

Add the CGXP submodule::

    git submodule add https://github.com/camptocamp/cgxp.git $PROJECT/static/lib/cgxp -b <version>
    git submodule foreach git submodule update --init

``-b <version>`` forces to use the CGXP branch ``<version>``.
Branches are available starting at version ``1.3``.

Commit and push on the main repository::

    git commit -m "initial commit"
    git push origin master

Configure the application
-------------------------

As the integrator you need to edit two files to configure the application:
``config.yaml.in`` and ``buildout.cfg``.

``config.yaml.in`` includes the *static configuration* of the application.  This
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

   To have a working PNG print you should get and edit the file
   ``print/WEB-INF/classes/imagemagick-mapfish-spring-application-context-override.xml``,
   get it::

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

   Some parts will not work or will not do anything on Windows, than add in
   your `buildout.cfg` file in the `[buildout]` section::

        parts -= fix-perm

    and in the `[template]` section::

        extends -= facts


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

Create a multi instance project
-------------------------------

In some cases we want to create applications based on very similar code and settings.

To be consistent with c2cgeoportal terminology we will use the words `project`
to refer to the whole project and `instance` for a dedicated configuration of
the project.

This procedure will deal with:

* One folder per instance ``mapfile/<instance>``.
* One configuration file for all the project ``config.yaml.in``.
* One configuration file for each instance ``config_<instance>.yaml.in``.
* One buildout file for all the project ``buildout.cfg``.
* One buildout file for each instance ``buildout_<instane>.cfg``.
* One buildout generator for each developer and server ``buildout_<user>.cfg.jinja``.
* One additional CSS file for each instance ``<project>/static/css/proj_<instance>.css``.

Create the project
..................

1. In ``setup.py`` add the following dependencies:

.. code:: python

   'bottle',
   'jinja2',

2. In ``setup.py`` add the following ``console_scripts``:

.. code:: python

   'gen_project_files = <project>.scripts.gen_project_files:main'

3. Create the generated project files from templates
   ``<project>/scripts/gen_project_files.py`` script:

.. code:: python

   # -*- coding: utf-8 -*-

   import yaml
   import glob
   import os
   from bottle import jinja2_template

   def main():
       config = yaml.load(open('config.yaml', 'r'))
       for template in glob.glob('*.jinja'):
           for instance in config['instances']:
               file_parts = template.split('.')
               file_name = "%s_%s.%s" % (file_parts[0], instance, '.'.join(file_parts[1:-1]))
               result = jinja2_template(
                   template,
                   instance=instance,
                   config=config,
               )
               file_open = open(file_name, 'w')
               file_open.write(result)
               file_open.close()

4. In ``buildout.cfg`` add a task to generate the buildout files:

.. code::

   [jinja-template]
   recipe = collective.recipe.cmd:py
   on_install = true
   on_update = true
   cmds =
       >>> from subprocess import call
       >>> from os.path import join
       >>> cmd = join('buildout', 'bin', 'gen_project_files')
       >>> call([cmd])

5. Define the developer templates as follows (``buildout_<user>.cfg.jinja``):

.. code::

   [buildout]
   extends = buildout_{{instance}}.cfg
   parts -= fix-perm

   [vars]
   instanceid = <user>-{{instance}}
   host = <host>

   [jsbuild]
   compress = False

   [jsbuild-mobile]
   compress = False

   [cssbuild]
   compress = false

6. Define the host templates as follows (``buildout_main.cfg.jinja``,
   ``buildout_demo.cfg.jinja``, ``buildout_prod.cfg.jinja``):

.. code::

   [buildout]
   extends = buildout_{{instance}}.cfg

   [vars]
   instanceid = ${vars:instance}
   apache-entry-point = /${vars:instanceid}/
   host = <host>

7. Create a ``config_<instance>.yaml.in`` file with:

.. code::

   page_title: <title>

   viewer:
        initial_extent: [<min_x>, <min_y>, <max_x>, <max_y>]
        restricted_extent: [<min_x>, <min_y>, <max_x>, <max_y>]
        default_themes:
        - <theme>
        feature_types:
        - <feature>

   functionalities:
        anonymous:
            print_template:
            - <template>

8. In ``<project>/__init__.py`` use the previous YAML file:

.. code:: python

    import collections
    import yaml

    def update(d, u):
        for k, v in u.iteritems():
            if isinstance(v, collections.Mapping):
                r = update(d.get(k, {}), v)
                d[k] = r
            else:
                d[k] = u[k]
        return d


    def main(global_config, **settings): # already defined
        ...
        settings = config.get_settings() # already defined
        project_settings = yaml.load(file(settings.get('app2.cfg')))
        if project_settings:
            update(settings, project_settings)

9. Define the instance buildout file ``buildout_<instance>.cfg`` as follows:

.. code::

   [buildout]
   extends = buildout.cfg

   [vars]
   instance = <instance>

10. In ``buildout.cfg`` define the vars as follows:

.. code::

   [vars]
   instance = to_be_overridden
   schema = ${vars:instance}
   instanceid = to_be_overridden
   parent_instanceid = to_be_defined
   host = to_be_overridden

These are placeholder variables which must be defined

11. In the ``buildout.cfg`` add the additional CSS:

.. code::

   [cssbuild]
   input +=
       <project>/static/css/proj_${vars:instance}.css

12. In the ``<project>/templates/index.html`` file do the following changes:

.. code:: diff

   -        <meta name="keywords" content="<project>, geoportal">
   -        <meta name="description" content="<project> Geoportal Application.">
   +        <meta name="keywords" content="${request.registry.settings['instance']}, geoportal">
   +        <meta name="description" content="${request.registry.settings['page_title']}.">

   -        <title><project> Geoportal Application</title>
   +        <title>${request.registry.settings['page_title']}</title>

            <link rel="stylesheet" type="text/css" href="${request.static_url('<project>:static/css/proj-widgets.css')}" />
   +        <link rel="stylesheet" type="text/css" href="${request.static_url('<project>:static/css/proj_%s.css' % request.registry.settings['instance'])}" />

13. Create the instance CSS file ``<project>/static/css/proj_<instance>.css``:

.. code:: css

   #header-in {
       background: url('../images/<instance>_banner_left.png') top left no-repeat;
       height: <height>px;
   }
   header-out {
       background: url('../images/<instance>_banner_right.png') top right no-repeat;
       background-color: #<color>;
       height: <height>px;
   }

14. In ``config.yaml.in`` define the following attributes:

.. code:: yaml

   # list of instance(s) for the project
   instances:
       - <instance>
       - <another_instance>
       - <as_many_instance_as_wanted>

   instance: ${vars:instance}

   external_themes_url: http://${vars:host}/${vars:parent_instanceid}/wsgi/themes
   external_mapserv_url: http://${vars:host}/${vars:parent_instanceid}/mapserv

   tilecache_url: http://${vars:host}/${vars:parent_instanceid}/wsgi/tilecache

15. In the files ``<project>/templates/api/mapconfig.js``,
    ``<project>/templates/viewer.js`` and ``<project>/templates/edit.js``
    define the ``WMTS_OPTIONS`` url as follows:

.. code:: javascript

   var WMTS_OPTIONS = {
       url: '${tilecache_url}',
       ...
    }

16. In ``apache/mapserver.conf.in`` file do the following change:

.. code:: diff

   -   SetEnv MS_MAPFILE ${buildout:directory}/mapserver/c2cgeoportal.map
   +   SetEnv MS_MAPFILE ${buildout:directory}/mapserver/${vars:instance}/c2cgeoportal.map

17. Edit ``deploy/deploy.cfg.in`` as follows:

.. code:: diff

    [DEFAULT]
   -project = ${vars:project}
   +project = ${vars:instance}

    [code]
   -dir = /var/www/vhosts/<project>/private/<project>
   +dir = /var/www/vhosts/<project>/private/${vars:instance}

    [apache]
   -dest = /var/www/vhosts/<project>/conf/<project>.conf
   -content = Include /var/www/vhosts/<project>/private/<project>/apache/*.conf
   +dest = /var/www/vhosts/<project>/conf/${vars:instance}.conf
   +content = Include /var/www/vhosts/<project>/private/${vars:instance}/apache/*.conf

18. In ``production.ini.in`` and ``developement.ini.in``
    add the following value:

.. code::

   [app:app]
   app2.cfg = %(here)s/config_${instance}.yaml

19. In ``.gitignore`` add the following lines:

.. code::

   config_*.yaml
   buildout_*_*.cfg
   mapserver/*/*.map
   mapserver/*/*/*.map


Result
......

Now you can configure the application at instance level in the following places:

* ``mapserver/<instance>``
* ``buildout_<instance>.cfg``
* ``mandant/static/images/<instance>_banner_right.png``
* ``mandant/static/images/<instance>_banner_left.png``
* ``mandant/static/css/proj_<instance>.css``
* ``config_<instance>.yaml.in``

To generate the configuration files, run the following command:

.. code::

   ./buildout/bin/buildout install eggs template jinja-template

then run the buildout command with the .cfg file for the instance you want to setup:

.. code::

   ./buildout/bin/buildout -c buildout_<user>_<instance>.cfg
