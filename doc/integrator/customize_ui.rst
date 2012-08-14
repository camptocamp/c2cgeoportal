.. _integrator_customize_ui:

Customize the UI
================

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
especially building a
`gxp.Viewer <http://gxp.opengeo.org/master/doc/lib/widgets/Viewer.html>`_
object (``app = new gxp.Viewer({ ... });``).
In its configuration we have tree important sections:

``portalConfig``
~~~~~~~~~~~~~~~~

The portal configuration assembles Ext components especially the containers,
to describe the application layout.

``tools``
~~~~~~~~~

Most of the tools used in the application are
`cgxp.plugins <http://docs.camptocamp.net/cgxp/lib/plugins.html>`_.

In most cases code examples to add to the ``viewer.js`` file are available.
Don't forget to add the plugin files in your ``jsbuild/app.cfg`` file.
For example, to use the Legend panel, add::

    [app.js]
    ...
    include =
        ...
        CGXP/plugins/Legend.js

``map``
~~~~~~~

See ``map`` section from
`gxp.Viewer documentation <http://gxp.opengeo.org/master/doc/lib/widgets/Viewer.html>`_

