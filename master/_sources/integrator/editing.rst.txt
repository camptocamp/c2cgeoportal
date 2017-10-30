.. _integrator_editing:

Editing (with CGXP)
===================

Any c2cgeoportal application comes with an editing interface, available at
``/edit`` (assuming ``/`` is the application's root URL).

The editing interface requires the editing plugin (``cgxp.plugins.Editing``),
which is provided by CGXP as of commit `58c931d
<https://github.com/camptocamp/cgxp/commit/58c931de2f6397ffba223b4305d0b10a18413032>`_.
Make sure your application uses an appropriate version (commit) of CGXP.

The editing interface is defined in the application's ``templates/edit.html``
and ``templates/edit.js`` files.  The integrator can edit
``templates/edit.html`` and ``templates/edit.js`` to customize the editing
interface.

The integrator will probably need to:

* Add base layers.
* Change the map settings (``projection``, ``resolutions``, etc.).

Other customizations, like adding tools to the toolbar, can be done. If layer
sources and tools are added you will certainly need to edit ``jsbuild/app.cfg``
and add scripts in the ``[edit.js]`` sections.

See the `Editing API doc
<http://docs.camptocamp.net/cgxp/2.3/lib/plugins/Editing.html>`_ for the list of
options the plugin can receive.


Limitations
-----------

At the moment only fields of type ``datetime`` and ``date`` are supported. ``time`` is NOT supported.

Validation
----------

Checking the validity of a geometry may be enabled using the following
configuration in ``vars_<project>.yaml``:

.. code:: yaml

   vars:
       ...
       layers:
           geometry_validation: True
