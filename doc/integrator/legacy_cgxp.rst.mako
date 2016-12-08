.. _integrator_cgxp:

CGXP
====

In recent versions of GeoMapFish, `CGXP` has been replaced by `ngeo` to propose
a more modern interface to the end user. It is still possible to keep using
`CGXP` though.

Use the CGXP interface
----------------------

If you are currently upgrading your application and want to keep using `CGXP`,
the following changes are required.

``index.html`` and ``viewer.js`` files need to be renamed to ``desktop.html``
and ``desktop.js`` respectively.

.. prompt:: bash

  git mv <package>/templates/index.html <package>/templates/desktop.html
  git mv <package>/templates/viewer.js <package>/templates/desktop.js

Then apply the following changes in the ``<package>/templates/desktop.html``
file:

.. code:: diff

  - % for script in Merger.from_fn(jsbuild_cfg, root_dir=jsbuild_root_dir).list_run(['app.js', 'lang-%s.js' % lang]):
  + % for script in Merger.from_fn(jsbuild_cfg, root_dir=jsbuild_root_dir).list_run(['desktop.js', 'lang-%s.js' % lang]):

  - <script type="text/javascript" src="${'$'}{request.static_url('<package>:static/build/app.js')}"></script>
  + <script type="text/javascript" src="${'$'}{request.static_url('<package>:static/build/desktop.js')}"></script>
  ...
  - <script type="text/javascript" src="${'$'}{request.route_url('viewer', _query=extra_params)}"></script>
  + <script type="text/javascript" src="${'$'}{request.route_url('desktop.js', _query=extra_params)}"></script>

Finally apply the following change in ``jsbuild/app.cfg.mako``:

.. code:: diff

  - [app.js]
  + [desktop.js]

To configure the build of the interface you should set the ``CGXP_INTERFACES`` (and the ``NGEO_INTERFACES``)
in your project makefile, e.g.:

.. code:: make

  CGXP_INTERFACES = desktop edit routing
  NGEO_INTERFACES = mobile

You will also need to enable the `CGXP` checker. To do so, add this to your
project vars file:

.. code:: yaml

  vars:
      ...
      checker:
         ...
         defaults:
             ...
             lang_files: [cgxp]
  update_paths:
  ...
  - checker.defaults.lang_files

Make also sure that you do not have ``check_collector.disabled`` in the
``update_paths`` (and do not readd it during the next upgrade steps).

Then update the interface in your ``<package>/__init__.py`` file:

.. code:: diff

  - from c2cgeoportal import locale_negotiator, add_interface, INTERFACE_TYPE_SENCHA_TOUCH
  + from c2cgeoportal import locale_negotiator, add_interface, INTERFACE_TYPE_SENCHA_TOUCH, INTERFACE_TYPE_CGXP

Also add the following line:

.. code:: python

  add_interface(config, "desktop", INTERFACE_TYPE_CGXP)

``externalWFSTypes`` does not exist anymore so you should remove the following line
from ``<package>/templates/desktop.js``

.. code:: javascript

  externalWFSTypes: ${'$'}{externalWFSTypes | n},

Do the following change in the ``<package>/templates/desktop.html`` file:

.. code:: diff

   - ${'%'} if not no_redirect and mobile_url is not None:
   + ${'%'} if "no_redirect" not in request.params:
     <script>
         if(('ontouchstart' in window) || window.DocumentTouch && document instanceof DocumentTouch) {
   -         window.location = "${'$'}{mobile_url}";
   +         window.location = "${'$'}{request.route_url('mobile', _query=dict(request.GET))}";
         }
     </script>
     ${'%'} endif

The OGC proxy is deprecated because with modern browsers it is not required anymore.
You can simply remove the following line in  ``desktop.js``, ``edit.js`` and
``routing.js`` (in ``<package>/templates``).

.. code:: javascript

  OpenLayers.ProxyHost = "${'$'}{request.route_url('ogcproxy') | n}?url=";

Add the new oldPassword field:
You should add the following line in ``desktop.js``, ``edit.js`` and
``routing.js`` (in ``<package>/templates``).

.. code:: diff

     <input id="password" name="password" type="password" autocomplete="on"/>
   + <input id="oldPassword" name="oldPassword" type="password" />
     <input id="newPassword" name="newPassword" type="password" />

More information about how to configure the interface when using `CGXP` can be
found `here <https://camptocamp.github.io/c2cgeoportal/1.6/integrator/customize_ui.html>`_.

Back to the ngeo interface
--------------------------

Follow the above instructions if you want to use `ngeo` instead of `CGXP`.

.. prompt:: bash

  git rm <package>/templates/desktop.html
  git rm <package>/templates/desktop.js

Remove the related section in the ``jsbuild/app.cfg.mako`` file.

Update the interface in your ``<package>/__init__.py`` file
by removing the following line:

.. code:: python

  add_interface(config, "desktop", [INTERFACE_TYPE_CGXP])

To add an ngeo interface see :ref:`integrator_ngeo_add`.

If you remove all the `CGXP` interface, remove the ``vars.checker.defaults.lang_files`` from your
project vars file, and the ``checker.defaults.lang_files`` from your update_paths.
