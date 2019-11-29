.. _integrator_admin_interface:

Configure the admin interface
=============================

You can activate or deactivate (tabs, modules, models or tables) in administration interface using configuration key ``exclude_pages`` and ``include_pages``.


Include and excludes tabs
-------------------------

Default tabs/modules
~~~~~~~~~~~~~~~~~~~~

The active default tabs (route urls) are:
- layertree
- themes
- layer_groups
- layers_wms
- layers_wmts
- ogc_servers
- restriction_areas
- users
- roles
- functionalities
- interfaces


Optional tabs/modules
~~~~~~~~~~~~~~~~~~~~~

There are optional tabs, not available if not explicitly included.

The list is:
- layers_vectortiles


Include a new page
~~~~~~~~~~~~~~~~~~

We need a url path and a class to include a new page.

Here is an example using the existing vector tiles page:

.. code:: yaml

  vars:
    admin_interface:
      include_pages:
        - [layers_vectortiles, c2cgeoportal_commons.models.main.LayerVectorTiles]

.. note::

   It is possible also to add totally new tables, models, tabs.


Exclude a page
~~~~~~~~~~~~~~

We can exclude any of the default tabs.
The syntax use a list under ``vars/admin_interface/exclude_pages``.
