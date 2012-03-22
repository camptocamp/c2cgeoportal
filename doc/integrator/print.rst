.. _print:

============================
Print config.yaml templating
============================

Introduction
------------

All print-related files are located in the ``print/`` folder.

The main file (``print/config.yaml``) used to define your print template written in YAML format.

 * `YAML on Wikipedia <http://en.wikipedia.org/wiki/YAML>`_
 * `The official YAML site <http://www.yaml.org/>`_
 * `Mapfish print configuration documentation 
   <http://mapfish.org/doc/print/configuration.html>`_
 * `YAML validator <http://yaml-online-parser.appspot.com/>`_


Mako templating
---------------

If you intend to have more than one paper format for your PDF
print output, a templating system is implemented to allow you to use mako
template so you don't have to duplicate a huge quantity of code in your ``print/config.yaml``.

The system checks if there is a file "print.mako" in a folder ``print/templates/`` in 
the ``print/`` folder (``print/templates/print.mako``).
If that file exists, it will be used to generate the file ``print/config.yaml`` placed 
in the ``print/`` folder.
If the file does not exist, the system does nothing.

It is possible to manually trigger the system by calling the following command::

    ./buildout/bin/print_tpl

If you want to include some buildout variables in your mako template, you need to 
add a .in extension to your mako template(s) as the variable replacement must be done 
before the mako templating is called (for example print/templates/print.mako.in)

In the default template we have two base print template A4_portrait.mako and
A3_landscape.mako where we have some blocks like::

    <%def name="title()">\
    1 A4 portrait\
    </%def>

And in ``print/templates/A3_landscape_inherit.mako`` and 
``print/templates/A4_portrait_inherit.mako`` thoses block will 
be redefined.
The ``print.mako.in`` has the "header" part and includes the wanted templates.

Using BackgroundPDF parameter
------------------------------


In print configuration you can use a PDF as a background image. You should put the 
PDF file in the print directory and use '<%text>$</%text>{configDir}/tpl_puidoux.pdf' 
for the valeur of BackgroundPDF parameter.

In your buildout.cfg file you should add this parts:

::
   
   [print-war]
   input += *.pdf

