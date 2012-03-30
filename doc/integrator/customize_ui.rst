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

The viewer.js configure all the client application, 
the main build class is documented there:
`gxp.Viewer <http://gxp.opengeo.org/master/doc/lib/widgets/Viewer.html>`_.

The most important part is the ``tools``, most of them where get from 
`cgxp.plugins <http://docs.camptocamp.net/cgxp/lib/plugins.html>`_.
