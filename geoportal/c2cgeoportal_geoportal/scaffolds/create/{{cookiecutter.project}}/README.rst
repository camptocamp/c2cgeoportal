{{cookiecutter.project}} project
===================

Read the `Documentation <https://camptocamp.github.io/c2cgeoportal/{{cookiecutter.geomapfish_main_version}}/>`_

Checkout
--------

.. code::

   git clone git@github.com:camptocamp/{{cookiecutter.project}}.git

   cd {{cookiecutter.project}}

Build
-----

.. code::

  ./build

Run
---

.. code::

   docker compose up -d

Contributing
------------

Install the pre-commit hooks:

.. code-block:: bash

   pip install pre-commit
   pre-commit install --allow-missing-config --config=.pre-commit-config.yaml

.. Feel free to add project-specific things.
