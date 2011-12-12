
.. _print:

============================
Print config.yaml templating
============================

If you intend to have more than one paper format for your PDF
print output, a templating system is implemented to allow you to use mako
template so you dont have to duplicate huge quantiy of code in your config.yaml.

The system checks if there is a file "print.mako" in a folder "templates" in 
the "print" folder (print/templates/print.mako).
If that file exists, it will be used to generate the file "config.yaml" placed 
in the "print" folder.
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

And in A3_landscape_inherit.mako and A4_portrait_inherit.mako thoses block will 
be redefined.
The print.mako.in has the "header" part and includes the wanted templates.
