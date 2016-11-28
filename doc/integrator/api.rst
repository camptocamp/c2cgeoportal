.. _integrator_api:

JavaScript API
==============

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
the target project, and copying the missing files from there:

.. prompt:: bash

    cd <project>
    .build/venv/bin/pcreate -s c2cgeoportal_create \
            /tmp/<project> package=<package>
    cp -r /tmp/<project>/<package>/templates/api <project>/templates/
    cp -r /tmp/<project>/<package>/static/apihelp <project>/static/
    rm -rf /tmp/<project>

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

Gotchas, limitations and hints
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Below are a few things that c2cgeoportal integrators should know and take into
account when setting up their projects' APIs.

Background/base layers

    Several notes about background/base layers.

    As mentioned already the background/base layers are defined in the map
    configuration, in ``<package>/templates/api/mapconfig.js``.

    Any ``displayLayerSwitcher`` option set in the ``args`` property of the
    base layers defined in the map config is ignored. The API itself is
    responsible for setting this option. The Simple API sets
    ``displayLayerSwitcher`` to ``true``, while the Extended API sets it to
    ``false``.

    To control the display of base layers through the UI when the Extended API
    is used the ``MapOpacitySlider`` plugin should be set in the viewer. The
    OpenLayers ``LayerSwitcher`` control will indeed not include base layers
    (and radio buttons) in the case of the Extended API.

    The API user can also have some control on his map's base layers, through
    the ``backgroundLayers`` option, which is optional.

    The ``backgroundLayers`` option references an array of layer
    names/references, which should correspond to the ``ref`` values in the map
    config.

    The ``backgroundLayers`` option determines the set of layers to add to the
    map. It also determines the order of layers in the map, but the behavior is
    different in API and XAPI.

    For the Simple API every layer in the map config is an OpenLayers base
    layer. By setting ``backgroundLayers`` the API user specifies the base
    layers the map will work with, and the order of the base layers in the
    map's layers array.  The first layer in the ``backgroundLayers`` option is
    the base layer that will be displayed by default.

    For the Extended API, if the viewer includes a map opacity slider plugin
    (``cgxp_mapopacityslider``), the backgroundLayers option has no effect on
    the layer order, and the background layer that is displayed by default.
    When the viewer includes a map opacity slider plugin the "background layer
    behavior" is indeed entirely determined by the plugin, and the user that
    controls the plugin through the UI.

    If the map opacity slider plugin (``cgxp_mapopacityslider``) is enabled,
    the layer visibility is managed by the plugin. Else the  layer
    ``visibility`` must be set  to ``true`` in
    ``<package>/templates/api/mapconfig.js``.

    When the viewer does not include a map opacity slider plugin the
    ``backgroundLayers`` option determines the order of layers in the map/layer
    store. But the layers marked as background layers in the map config are
    always before the other layers (non-background layers) in the map/layer
    store.

Layer tree

    Using the ``LayerTree`` plugin in the API viewer is highly discouraged.
    The API user (application developer) is responsible for declaring the
    layers he wants in his map. Adding a ``LayerTree`` plugin would conflict
    with that behavior, as the ``LayerTree`` plugin adds layers to the map
    based on the ``THEMES`` configuration.

Plugins compatible with the API

    Here is the list of CGXP plugins that are known to currently work with the
    Extended API:

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
    file is not used for the APIs, so it should not contain CSS that pertains
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
