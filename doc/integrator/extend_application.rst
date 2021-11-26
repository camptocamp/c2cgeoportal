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

If you need to configure your own authentication you will need to extend the ``geoportal`` Docker image.

For that you will need to create a new folder named ``geoportal_custom``.

An this folder, add a file named ``authentication.py`` with the content you need, the original content is:

.. code:: python:

   from pyramid.config import Configurator

   from pyramid.authorization import ACLAuthorizationPolicy
   from c2cgeoportal_geoportal.lib.authentication import create_authentication


   def includeme(config: Configurator) -> None:
       """
       Initialize the authentication( for a Pyramid app.
       """
       config.set_authorization_policy(ACLAuthorizationPolicy())
       config.set_authentication_policy(create_authentication(config.get_settings()))

Create a file named ``Dockerfile`` with the following content:

.. code::

   ARG GEOMAPFISH_MAIN_VERSION

   FROM camptocamp/geomapfish:${GEOMAPFISH_MAIN_VERSION} as runner

   COPY authentication.py /app/geomapfishapp_geoportal/

In the ``docker-compose.yaml`` file do the following changes:

.. code:: diff

       geoportal:
         extends:
           file: docker-compose-lib.yaml
           service: geoportal
   +     image: ${DOCKER_BASE}-geoportal:${DOCKER_TAG}
   +     build:
   +       context: geoportal_custom
   +       args:
   +         GIT_HASH: ${GIT_HASH}
   +         GEOMAPFISH_VERSION: ${GEOMAPFISH_VERSION}
   +         GEOMAPFISH_MAIN_VERSION: ${GEOMAPFISH_MAIN_VERSION}
         volumes_from:

.. warning::

   With these changes, you can add your own authentication logic, but be aware that this logic may need
   to be adapted when migrating to future versions of GeoMapFish.
