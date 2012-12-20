.. _integrator_api:

JavaScript API
==============

*New in c2cgeoportal 1.2.*

Any c2cgeoportal application exposes a JavaScript API. This API can be used in
third-party applications, like CMS applications. A c2cgeoportal application
actually exposes two JavaScript APIs: the *Simple* API, and the *Extended* API.
Both expose the same programming interface.

**Simple API**

    The Simple API does not include any Ext-related code, it is based on
    OpenLayers only. This API is to be used when a *simple* map only is needed.
    Also, the Simple API works in touch devices, while the Extended API does
    not.

    To load the Simple API in a page the following script tag should be added::

        <script src="http://example.com/path-to-wsgi-app/api.js"></script>

**Extended API**

    The Extended API is based on the CGXP stack (Ext/GeoExt/GXP) and plugins,
    just like the main (desktop) viewer. It provides more functionality than
    the Simple API, but it is heavier than the Simple API, and does not on
    mobile.

    To load the Extended API in a page the following script tag should be
    added::

        <script src="http://example.com/path-to-wsgi-app/xapi.js"></script>

.. note::

    CGXP commit `5c0628d
    <https://github.com/camptocamp/cgxp/commit/5c0628d05f4239ebf45419b19140badda9046c8b>`_
    or better is required in the project for the APIs.

Updating an existing project
----------------------------

You can skip this section if your project has been created using c2cgeoportal
1.2 or better. If your project was created using an older c2cgeoportal, and if
you've just upgraded your project to c2cgeoportal 1.2, then you need to follow
the below instructions.

New directories and files are provided by the ``c2cgeoportal_create`` and need
to be added manually to the project. The easiest way to get all the necessary
files involves creating a temporary c2cgeoportal project of the same name as
the target project, and copying the missing files from there::

    $ cd <project_name>
    $ ./buildout/bin/pcreate -s c2cgeoportal_create \
            /tmp/<project_name> package=<package_name>
    $ cp -r /tmp/<project_name>/<package_name>/templates/api <project_name>/templates/
    $ cp -r /tmp/<project_name>/<package_name>/static/apihelp <project_name>/static/
    $ rm -rf /tmp/<project_name>

Configuring the API
-------------------

As the integrator you will edit four Mako template files to configure the
APIs:

``<package>/templates/api/mapconfig.js``

    Includes the map configuration, i.e. the resolutions, the base layers, the
    controls, etc. Used for both the Simple and the Extended APIs.
    
``<package>/templates/api/viewer.js``

    Contains the GXP/CGXP viewer and plugins configuration. Used for the
    Extended API only.

``<package>/templates/api/api.js`` and ``<package>/templates/api/xapi.js``

    Include the loaders for the Simple API and the Extended API, respectively.
    For the map to be queryable (on click) you need to list the names of
    queryables WMS layers in the ``queryableLayers`` array. For example::

        this.queryableLayers = ['bike_tracks', 'interstates'];
    
    (This shouldn't be a manual operation. It is a manual operation right now
    because the ``OWSLib`` library doesn't read the ``queryable`` attribute
    from the WMS GetCapabilities document. See
    https://github.com/geopython/OWSLib/pull/41.)

Gotchas, limitations and hints
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Below are a few things that should be known and taken into account.

Any ``displayLayerSwitcher`` option set in the ``args`` property of the base
layers defined in the map config is ignored. The API itself is responsible for
setting this option. The Simple API sets ``displayLayerSwitcher`` to ``true``,
while the Extended API sets ``displayLayerSwitcher`` to ``false``.

To control the display of base layers when the Extend API is used the
``MapOpacitySlider`` plugin should be set in the viewer. The OpenLayers
``LayerSwitcher`` control will indeed not include base layers in the case of
the Extended API.

Using the ``LayerTree`` plugin in the API viewer is highly discouraged.  The
API user (application developer) is responsible for declaring the layers he
wants in his map. Adding a ``LayerTree`` plugin would conflict with that
behavior, as the ``LayerTree`` plugin adds layers to the map based on the
``THEMES`` configuration.

Here's the list of CGXP plugins that are known to currently work with
the Extended API:

* ``FullTextSearch``
* ``Legend``
* ``MapOpacitySlider``
* ``Measure``
* ``MenuShortcut``
* ``Zoom``
* ``ZoomToExtent``

CSS
---

Any c2cgeoportal application has its own CSS styles in
``<package>/static/css/proj.css``, ``<package>/static/css/proj-map.css``, and
``<package>/static/css/proj-widgets.css``. For the APIs it is important
that these files have appropriate contents.

``<package>/static/css/proj.css``

    This file includes CSS that is specific to the application viewers. This
    file is not used for the APIs, so it shouldn't contain CSS that pertains
    to OpenLayers and CGXP components used by the Simple and Extended APIs.

``<package>/static/css/proj-map.css``

    This file should include CSS that is relative to the OpenLayers map. This
    file is used by the Simple API. It should include OpenLayers-specific CSS,
    and should not include Ext-related CSS.

``<package>/static/css/proj-widgets.css``

    This file should include CSS for CGXP plugins/components used by the
    Extended API. This file is not used by the Simple API.

.. _integrator_api_i18n:

Internationalization
--------------------

The Simple API loads the files ``<package>/static/js/Proj/Lang/<code>.js``
(where ``<code>`` is the language code, ``fr`` for example). This means that
these files should not include GeoExt-based translations. More specifically
they should use ``OpenLayers.Util.extend(OpenLayers.Lang.<code>, {})`` and they
should not use ``GeoExt.Lang.add("<code>", {})``. GeoExt-based translations
should go in ``<package>/static/js/Proj/Lang/GeoExt-<code>.js`` files, which
are used for the application viewers and for the Extended API.
