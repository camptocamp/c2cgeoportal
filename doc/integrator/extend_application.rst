.. _extend_application:

Extend the application
======================

To add an additional component in the project in simple mode we should:

- use an interface in canvas mode
- add a custom docker-compose service
- add a custom JavaScript file

Interface in canvas mode
------------------------

Get the files from the ``CONST_create_template``:

.. prompt:: bash

    mkdir -p geoportal/interfaces/
    cp CONST_create_template/geoportal/interfaces/desktop_alt.html.mako \
        geoportal/interfaces/desktop.html.mako
    mkdir -p geoportal/<package>_geoportal/static/images/
    cp CONST_create_template/geoportal/<package>_geoportal/static/images/background-layer-button.png \
        geoportal/<package>_geoportal/static/images/

In the file ``geoportal/interfaces/desktop.html.mako`` your can see that there is some HTML tags that
have an attribute slot. The slot says where the component should be added:

- ``header`` -> in the header part of the page.
- ``data`` -> in the data panel on the left of the map.
- ``tool-button`` -> in the tools on the right of the map.
- ``tool-button-separate`` -> in the tools on the right of the map, for the shared button.
- ``tool-<panel-name>`` -> in the tools panel on the right of the map, when the tool is activated.
- ``footer-<panel-name>`` -> in the footer part of the page, when the panel is activated.

In the ``vars.yaml`` file your interface should be declared like that:

.. code:: yaml

   interfaces:
     - name: desktop
       type: canvas
       default: true

Custom docker-compose service
-----------------------------

Will be filled later.

Custom JavaScript file
----------------------

Will be filled later.

Extend the geoportal image
--------------------------

Will be filled later.
