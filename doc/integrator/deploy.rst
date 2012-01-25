.. _administrator_deploy:

Deploy the application
======================

The first tine you want do deploy an application the configuration 
should be setup in the file ``deploy/deploy.cfg[.in]``.

The deploy tool has four parts:

* ``[file]`` to deploy the GeoTIFF, ShapeFiles and so on.
* ``[database]`` to deploy the database.
* ``[code]`` to deploy the application.
* ``[apache]`` to build the apache config.

An other important section is the ``[remote_hosts]`` where we 
configure the demo and production hosts.


To deploy from dev to demo
--------------------------

Build on the dev server::

  ssh -A <dev_server> # SSH agent forward is needed
  cd /var/www/<your_vhost>/public/<your_project>
  svn up # update the code
  rm -rf buildout/parts/modwsgi # to prevent rights error
  ./buildout/bin/buildout -c buildout_main.cfg # configure c2cgeoportal

**Test on the dev server**
    
Deploy to the demo server::

  rm -rf buildout/parts/modwsgi # to prevent rights error
  cd deploy
  sudo -u deploy deploy -r deploy.cfg demo 
  ./buildout/bin/buildout -c buildout_main.cfg # to make dev working again

**Test on the demo server**

To deploy from demo to prod
---------------------------

**Test on the demo server**

Deploy on the prod server::

  ssh -A <demo_server> # SSH agent forward is needed
  cd /var/www/<your_vhost>/public/<your_project>
  cd deploy
  sudo -u deploy deploy -r deploy.cfg prod 

**Test on the prod server**

