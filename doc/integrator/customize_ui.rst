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

The ``viewer.js`` template is used to configure the client application.
It creates a
`gxp.Viewer <http://gxp.opengeo.org/master/doc/lib/widgets/Viewer.html>`_
object (``app = new gxp.Viewer({ ... });``) defining the application's UI.
The Viewer config includes three important sections:

``portalConfig``
~~~~~~~~~~~~~~~~

The portal configuration assembles Ext components (containers really),
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

Sub domain
----------

If you want to optimize the parallelization of static resource download you
can use sub domain to do that you should define in the ``config.yaml.in``
something like this::

    # The used sub domain for the static resources
    subdommains: ['s1', 's2', 's3', 's4']

Those sub domain should obviously be define in the DNS and in the Apache
vhost. If the application is served on deferent URL and you want to use
the sub domain on only one of them you can define in the ``config.yaml.in``
the following::

    # The URL template used to generate the sub domain URL
    # %(sub)s will be replaced by the sub domain value.
    subdomain_url_template: http://%(sub)s.${vars:host}
