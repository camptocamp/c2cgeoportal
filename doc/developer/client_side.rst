.. _developer_client_side:

Client-side development
=======================

Using an external library
-------------------------

Add a file named ``geoportal/package.json`` with:

.. code:: json

   {
     "name": "<a_name>",
     "version": "1.0.0",
     "description": "<a_description>",
     "dependencies": {
       "<package_name>": "<package_version>",
     }
   }

Add at the end of the ``Makefile``:

 .. code:: Makefile

    /build/apps.timestamp: custom-npm-packages
    custom-npm-packages:
        (cd geoportal && npm install)

In the ``docker-compose.override.sample.yaml`` file add in the ``webpack_dev_server`` service:

.. code:: yaml

   volumes:
     - ./geoportal/node_modules: /app/node_modules


Importing a single Javascript file from the package
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Add in the alias of the file ``geoportal/webpack.apps.js.mako``:

 .. code:: javascript

    alias: {
      ...,
      '<your_package_name>': path.resolve(__dirname, 'node_modules/<package_name>/<the_javascript>.js
    }

And use it with:

.. code:: javascript

  import '<your_package_name>';


Importing multiple Javascript files from the package
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Add in the alias of the file ``geoportal/webpack.apps.js.mako``:

 .. code:: javascript

    alias: {
      ...,
      '<your_package_name>': path.resolve(__dirname, 'node_modules/<package_name>/<src_folder?>
    }

And use it with:

.. code:: javascript

  import '<your_package_name>/<the_javascript>.js';
