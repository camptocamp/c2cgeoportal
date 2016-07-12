.. _build_doc:

Build this doc
==============

* Change to the ``doc`` directory::
  
  $ cd doc

* Create a virtual env::

  $ wget http://www.mapfish.org/downloads/virtualenv-1.4.5.py
  $ python virtualenv-1.4.5.py --distribute --no-site-packages env

* Activate the virtual env::

  $ source env/bin/activate

* Install Sphinx::

  $ pip install sphinx

* Build the doc::

  $ make html

The HTML should now be available in the ``_build/html`` directory.
