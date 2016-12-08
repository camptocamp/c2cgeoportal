.. _developer_principles:

Principles
==========

This section includes development principles and guidelines. It is important to
know and respect these principles, for ``c2cgeoportal`` as well as for projects
based on ``c2cgeoportal``.

* We want our code to be covered by automated tests.
* Do not use templating (``.mako`` extension) for files including code
  (``.py``, ``.js``, ``.css``, etc.) apart from the standard Pyramid templates
  (in ``<package>/templates/``).
