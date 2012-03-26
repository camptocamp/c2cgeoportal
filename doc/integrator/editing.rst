.. _integrator_editing:

Editing
=======

*New in c2cgeoportal 0.6.*

Any c2cgeoportal application comes with an editing interface, available at
``/edit`` (assuming ``/`` is the application's root URL).

The editing interface requires the editing plugin (``cgxp_editing``), which is
provided by CGXP as of commit `4423e4b
<https://github.com/camptocamp/cgxp/commit/4423e4b7f984745ac1341e6c00850bab74fe5a3d>`_.
So make sure your application uses an appropriate version (commit) of CGXP.

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
