.. _build_doc:

Build this doc
==============

* Change to the ``doc`` directory
  
  .. prompt:: bash

      cd doc

* Create a virtual env

  .. prompt:: bash

      virtualenv --distribute --no-site-packages env

  .. note::

     if virtualenv isn't installed you can also use:

     .. prompt:: bash

        wget http://www.mapfish.org/downloads/virtualenv-1.4.5.py
        python virtualenv-1.4.5.py --distribute --no-site-packages env

* Activate the virtual env

  .. prompt:: bash $,(env)...$ auto

     $ source env/bin/activate
     (env)...$

* Install requirements

  .. prompt:: bash $,(env)...$ auto

     (env)...$ pip install -r requirements.txt

* Build the doc

  .. prompt:: bash $,(env)...$ auto

     (env)...$ make html

* Deactivate the virtual env

  .. prompt:: bash $,(env)...$ auto

     (env)...$ deactivate 
     $

The HTML should now be available in the ``_build/html`` directory.
