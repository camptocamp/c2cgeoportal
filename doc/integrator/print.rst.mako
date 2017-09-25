.. _integrator_print:

Print
=====

Adding the *print* feature to a c2cgeoportal project involves adding
a ``cgxp.plugins.Print`` plugin to the viewer, and configuring the MapFish
Print.

The Print plugin
----------------

The viewer should include a ``Print`` plugin for the *print* feature to
be available in the user interface.

See the `Print API doc
<http://docs.camptocamp.net/cgxp/${main_version}/lib/plugins/Print.html>`_ for the
list of options the plugin can receive.

*The main viewer includes a Print plugin by default.*

Using MapFish Print v3
----------------------

Migration from the v2
~~~~~~~~~~~~~~~~~~~~~

Start the migration by instantiating the default template:

.. prompt:: bash

   cd <project_root>
   cp -r print ~
   git rm -r print
   SRID=-1 ./docker-run pcreate --interactive --scaffold c2cgeoportal_create --package-name <package> /tmp/<project>
   ./docker-run pcreate --interactive --scaffold c2cgeoportal_update --package-name <package> /tmp/<project>
   mv /tmp/<project>/print .
   rm -rf /tmp/<project>

Then in ``~/print`` you will have a backup of the old template, and in the ``print`` folder you will have the new print configuration.

In the ``<package>.mk`` you should remove the ``PRINT_VERSION = 2`` (it is ``3`` by default).

In the concerned viewer javascript files, in the ``cgxp_print`` plugin add the following lines:

.. code:: javascript

   version: 3,
   encodeLayer: {},
   encodeExternalLayer: {},
   additionalAttributes: []

Template configuration
~~~~~~~~~~~~~~~~~~~~~~

All print-related files are located in the ``print/`` folder, and the files related to the template in the
``print/print-apps/<package>`` folder.

The main configuration file is ``print/print-apps/<package>/config.yaml``.

* `MapFish print documntation <http://mapfish.github.io/mapfish-print-doc/>`_
* `Startup with Jasper Reports <http://mapfish.github.io/mapfish-print-doc/#/jasperReports>`_


MapFish Print v2 configuration
------------------------------

All print-related files are located in the ``print/`` folder.

The main file (``print/config.yaml``) used to define your print template written in YAML format.

* `YAML on Wikipedia <http://en.wikipedia.org/wiki/YAML>`_
* `The official YAML site <http://www.yaml.org/>`_
* `Mapfish print configuration documentation
  <http://mapfish.org/doc/print/configuration.html>`_
* `YAML validator <http://yaml-online-parser.appspot.com/>`_

Spec attributes
~~~~~~~~~~~~~~~

With CGXP we have the following spec attributes:

On each page:

* ``center`` Center (standard).
* ``rotation`` Map rotation (standard).
* ``scale`` Scale (standard).
* ``showMap`` Used to show the map.
* ``showMapframe`` Used to show the border on the map page. [#map]_
* ``showNorth`` Used to show the arrow on the map page. [#map]_
* ``showScale`` Used to show the scale bar on the map page. [#map]_
* ``showScaleValue``  Used to show the scale on the map page. [#map]_
* ``showAttr`` Used to show the table on the query result pages. [#query]_
* ``showMapQueryResult`` Not used, true for the query result pages. [#query]_
* ``col0`` - ``coln``: Column tiles for the query result pages.
* ``table``: Query result table.

.. [#map] is ``true`` on the map page and ``false`` on query result pages
.. [#query] is ``true`` on the query result pages and ``false`` on map page

Global:

* ``dpi`` The DPI (standard).
* ``layout`` The used layout (standard).
* ``srs`` The EPSG code (standard).
* ``unit`` The unit (standard).
* ``legend`` The legend (standard).
* ``title`` The document title.
* ``comment`` The document description.

.. note::

   If you use Mako templates for generating the print configuration,
   to prevent character '${'$'}' from being incorrectly interpreted, use
   ``<${'%'}text>${'$'}</${'%'}text>{attribute}`` in place of ``${'$'}{attribute}``.


Mako templating
~~~~~~~~~~~~~~~

If you intend to have more than one paper format for your PDF
print output, a templating system is implemented to allow you to use mako
template so you do not have to duplicate a huge quantity of code in your ``print/config.yaml``.

In the default template we have two base print template ``A4_portrait.mako`` and
``A3_landscape.mako`` where we have some blocks like:

.. code:: mako

    <${'%'}def name="title()">\
    1 A4 portrait\
    </${'%'}def>

And in ``print/templates/A3_landscape_inherit.mako`` and
``print/templates/A4_portrait_inherit.mako`` thoses block will
be redefined.

The ``print.yaml.mako`` has the "header" part and includes the wanted templates.


Using backgroundPdf parameter
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In print configuration you can use a PDF as a background image. You should put the
PDF file in the print directory and use
``<${'%'}text>${'$'}</${'%'}text>{configDir}/template_A4_portrait.pdf``
for the value of backgroundPdf parameter.

The ``print.yaml.mako`` has the "header" part and includes the wanted templates.


Using a single print server in a set of sites
----------------------------------------------

For memory issues it is recommended to only use a single print server for a set of sites.

For that we need to have only one ``vars_<project>.yaml`` which can easily be
generated by the templating. Then we should do:

* Remove the print from the ``children`` projects by
  removing the ``print`` folder:

  .. prompt:: bash

    git rm print

* Deactivate the print compilation by adding the following lines
  in the ``<package>.mk`` file:

  .. code:: make

    PRINT_VERSION = NONE

* Point to the parent print server by editing the following lines
  in the ``vars_<package>.yaml`` file:

  .. code:: yaml

    vars:
        ...
        # For print proxy
        # This value means that we use the parent print server
        print_url: http://{host}:8080/print/pdf/

* If needed set the print templates used by anonymous users by adding the
  following in the application configuration (``vars_<package>.yaml``):

  .. code:: yaml

     vars:
       ...
       functionalities:
           anonymous:
               print_template:
               - 1 A4 child
               - 2 A3 child

.. note::

   This system works for print v2 but must be adapted for
   print v3 (although that is the same idea).

Having a dedicated print instance
---------------------------------

The goal is to be able to create a custom makefile with which one we make:

.. prompt:: bash

   make -f <file>.mk

To have only the print.

For this, create a makefile with:

.. code:: yaml

   BUILD_RULES = test-packages print
   TEST_PACKAGES = main print
