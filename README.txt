
Installation of a new project instance
======================================

If we use the parent child concept:
$global_project is the name of the common part of all project, it can be 'project'.
$specific_project is the name of the subproject.
    global_project=project
    specific_project=commune
    package=package=$global_project

Otherwise:
$specific_project is the name of the project.
package=$global_project should be removes.
    global_project=project
    specific_project=$global_project
    package=


Procedure
---------

* Get c2cgeoportal and c2cmapfish utils
    $ svn export https://project.camptocamp.com/svn/c2c_mapfish/c2cgeoportal/trunk c2cgeoportal
    $ svn export https://project.camptocamp.com/svn/c2c_mapfish/c2cmapfish/trunk/util/ c2cutil

* Create a virtualenv, and activate it
    $ python c2cutil/virtualenv-1.4.5.py --distribute --no-site-packages env
    $ source env/bin/activate
    
* Install c2cgeoportal and its dependencies in the virtualenv
    (env) $ cd c2cgeoportal; python setup_install.py develop; cd -

* Create the project ('IOError: No egg-info directory found (...)' should be ignore)
    (env) $ paster create --template=c2cgeoportal_create $specific_project $package
    (env) $ paster create --template=c2cgeoportal_update $specific_project $package
  You need to provide an SRID. For EPSG:21781 enter 21781.

* Cleanup
    (env) $ deactivate
    $ rm -rf $specific_project/$global_project.egg-info
    $ rm -rf c2cgeoportal
    $ rm -rf c2cutil

* Go to the project directory
    cd $specific_project

* Get the right buildout file,
  for parent:
    rm buildout.cfg
    mv buildout_parent.cfg buildout.cfg
  for child:
    rm buildout_parent.cfg

* Import project into SVN (use the path you want).
    cd ..
    svn import -m "add $specific_project" $specific_project https://project.camptocamp.com/svn/$global_project/trunk/$specific_project
    rm -rf $specific_project
    svn co https://project.camptocamp.com/svn/$global_project/trunk/$specific_project
    cd -

* Link to c2cgeoportal:
    svn propset svn:externals "c2cgeoportal https://project.camptocamp.com/svn/c2c_mapfish/c2cgeoportal/trunk" .
    svn up

* Add svn:ignore:
    svn propset svn:ignore ".installed.cfg" .
    svn propset svn:ignore "*" buildout
    svn propset svn:ignore "deploy.cfg" deploy
    svn propset svn:ignore "*.map" mapserver
    svn propset svn:ignore "*.war
config.yaml" print
    svn propset svn:ignore "tilecache.cfg" tilecache
    svn propset svn:ignore "cgxp" $specific_project/static/lib
* Commit
    svn ci -m "setup of $specific_project"

