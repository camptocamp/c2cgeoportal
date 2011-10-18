
Installation of a new project instance
======================================

* Get c2cgeoportal and c2cmapfish utils
    $ svn export https://project.camptocamp.com/svn/c2c_mapfish/c2cgeoportal/trunk c2cgeoportal
    $ svn export https://project.camptocamp.com/svn/c2c_mapfish/c2cmapfish/trunk/util/ c2cutil

* Create a virtualenv, and activate it
    $ python c2cutil/virtualenv-1.4.5.py --distribute --no-site-packages env
    $ source env/bin/activate
    
* Install c2cgeoportal and its dependencies in the virtualenv
    (env) $ cd c2cgeoportal; python setup_install.py develop; cd -

* Create the project ('IOError: No egg-info directory found (...)' should be ignore)
    (env) $ paster create --template=c2cgeoportal_create specific_project package=global_project
    (env) $ paster create --template=c2cgeoportal_update specific_project package=global_project

* Cleanup
    (env) $ deactivate
    $ rm -rf specific_project/global_project.egg-info
    $ rm -rf c2cgeoportal
    $ rm -rf c2cutil

* Get the right buildout file,
  for parent:
    rm buildout_child.cfg
  for child:
    rm buildout.cfg
    mv buildout_child.cfg buildout.cfg

* Import project into SVN
    svn import specific_project https://project.camptocamp.com/svn/global_project/trunk/specific_project
    rm -rf specific_project
    svn co https://project.camptocamp.com/svn/global_project/trunk/specific_project

* Link to c2cgeoportal:
    svn propset svn:externals "c2cgeoportal https://project.camptocamp.com/svn/c2c_mapfish/c2cgeoportal/trunk" .
    svn propset svn:externals "cgxp https://project.camptocamp.com/svn/c2c_mapfish/cgxp" global_project/static/lib

* Add svn:ignore:
    svn propset svn:ignore ".installed.cfg" .
    svn propset svn:ignore "*" buildout
    svn propset svn:ignore "deploy.cfg" deploy
    svn propset svn:ignore "*.map" mapserver
    svn propset svn:ignore "*.war
config.yaml" print
    svn propset svn:ignore "tilecache.cfg" tilecache
* Commit
    svn ci -m "initial commit of global_project"
