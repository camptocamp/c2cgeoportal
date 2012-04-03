.. _integrator_customize_ui:

Customize the UI
================

*To Be Done* 

Organisation
------------

The main page where we can redefine the header 
is in the file: ``<package>/templates/index.html``.

The viewer (map and all related tools) 
is define in the file: ``<package>/templates/viewer.js``.

The sample for the API is in the file: 
``<package>/templates/apiviewer.js``.

The style sheet file is: ``<package>/static/css/proj.css``

And finally the image should be placed in the folder:
``<package>/static/images/``

Viewer.js
---------

The ``viewer.js`` template is used to configure the client application, 
especially using a 
`gxp.Viewer <http://gxp.opengeo.org/master/doc/lib/widgets/Viewer.html>`_ 
object.

Most of the tools used in the application are 
`cgxp.plugins <http://docs.camptocamp.net/cgxp/lib/plugins.html>`_.
