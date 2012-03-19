.. _integrator_editing:

Editing
=======

Any c2cgeoportal application comes with an editing interface, available at
``/edit`` (assuming ``/`` is the application's root URL).

The editing interface is defined in the application's ``templates/edit.html``
and ``templates/edit.js`` files.

The integrator can edit ``templates/edit.html`` and ``templates/edit.js`` to
customize the editing interface.

The integrator will probably need to:

 * Add base layers.
 * Change the map settings (``projection``, ``resolutions``, etc.).

Other customization like adding tools to the toolbar can be done. If layer
sources and tools are added you will certainly need to edit ``jsbuild/app.cfg``
and add scripts in the ``[edit.js]`` sections.
