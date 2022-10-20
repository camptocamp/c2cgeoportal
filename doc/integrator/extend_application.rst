.. _extend_application:

Extend the application
======================

To add an additional component in the project in simple mode we should:

- use an interface in canvas mode
- add a custom docker-compose service
- add a custom JavaScript file

In this tutorial, we will:

- Create a new Docker image for the new service
- Integrate it to the project
- Create the new interface based on canvas
- Create a new WebComponent
- Build it in the config image
- Add it to the interface template
- Debugging Custom JavaScript and service


Create a new Docker image for the new service
---------------------------------------------

In this chapter we will create a new Pyramid application that uses Cornice in a Docker image.

We will use the Pyramid Cookiecutter starter, we can use it directly
(by running ``cookiecutter gh:Pylons/pyramid-cookiecutter-starter``) if you want to do your
image by your own, but in this tutorial we will get the files directly from the demo.
For that run the following command:

.. prompt:: bash

   cd /tmp
   git clone git@github.com:camptocamp/demo_geomapfish.git
   cd -
   cp --recursive /tmp/demo_geomapfish/custom /tmp/demo_geomapfish/haproxy .

Add in ``.prettierignore`` the following line:

.. code::

   custom/Pipfile.lock

Apply the following diff in the ``setup.cfg``:

.. code:: diff

   - known_first_party=c2cgeoportal_commons,c2cgeoportal_geoportal,c2cgeoportal_admin,geomapfish_geoportal
   + known_first_party=c2cgeoportal_commons,c2cgeoportal_geoportal,c2cgeoportal_admin,geomapfish_geoportal,custom

.. note::

    The important files are:

    - The Database model `custom/custom/models/feedback.py <https://github.com/camptocamp/demo_geomapfish/blob/master/custom/custom/models/feedback.py>`_
    - The view `custom/custom/views/feedback.py <https://github.com/camptocamp/demo_geomapfish/blob/master/custom/custom/views/feedback.py>`_

Integrate it to the project
---------------------------

Add the following service in the ``docker-compose.yaml``, with that we will be able to build and run the image:

.. code:: yaml

  custom:
    image: ${DOCKER_BASE}-custom:${DOCKER_TAG}
    build:
      context: custom
      args:
        GIT_HASH: ${GIT_HASH}
    environment:
      - VISIBLE_WEB_HOST
      - GEOPORTAL_INTERNAL_URL
      - PGSCHEMA
      - SQLALCHEMY_POOL_RECYCLE
      - SQLALCHEMY_POOL_SIZE
      - SQLALCHEMY_MAX_OVERFLOW
      - SQLALCHEMY_SLAVE_POOL_RECYCLE
      - SQLALCHEMY_SLAVE_POOL_SIZE
      - SQLALCHEMY_SLAVE_MAX_OVERFLOW
      - SQLALCHEMY_URL=postgresql://${PGUSER}:${PGPASSWORD}@${PGHOST}:${PGPORT}/${PGDATABASE}?sslmode=${PGSSLMODE}
      - SQLALCHEMY_SLAVE_URL=postgresql://${PGUSER}:${PGPASSWORD}@${PGHOST_SLAVE}:${PGPORT_SLAVE}/${PGDATABASE}?sslmode=${PGSSLMODE}

Add the following service in the ``docker-compose.override.sample.yaml``, To be able to run the service
in debugging mode with auto reloading:

.. code:: yaml

  custom:
    command:
      - /usr/local/bin/pserve
      - --reload
      - c2c://development.ini
    volumes:
      - ./custom/custom:/app/custom

.. note::

   If you need the user credentials, you can do:

   .. code:: python

      requests.get(
          "http://geoportal:8080/loginuser",
          headers={"Cookie": request.headers.get("Cookie"), "Referrer": request.referrer},
      ).json()


Create the new interface based on canvas
----------------------------------------

Get the files from the ``CONST_create_template``:

.. prompt:: bash

    mkdir -p geoportal/interfaces/
    cp CONST_create_template/geoportal/interfaces/desktop_alt.html.mako \
        geoportal/interfaces/desktop.html.mako
    mkdir -p geoportal/<package>_geoportal/static/images/
    cp CONST_create_template/geoportal/<package>_geoportal/static/images/background-layer-button.png \
        geoportal/<package>_geoportal/static/images/

In the ``vars.yaml`` file your interface should be declared like that:

.. code:: yaml

   interfaces:
     - name: desktop
       type: canvas
       layout: desktop
       default: true

The ``name`` is the interface name as usual.
The ``type`` should be set to 'canvas' to be able to get the canvas based interface present in the config image.
The ``layout`` is used to get the JavaScript and CSS files from ngeo.
The ``default`` is used to set the default interface as usual.

In the file ``geoportal/interfaces/desktop.html.mako`` you will use the following variables:

- ``request`` -> the Pyramid request.
- ``header`` -> the header additional part of the page, the ``dynamicUrl`` and ``interface`` meta, and the CSS inclusion.
- ``spinner`` -> the spinner SVG image content.
- ``footer`` -> the footer additional part of the page, for the JavaScript inclusion.

You can also see that there is some HTML tags that have an attribute slot.
The slot says where the component should be added:

- ``header`` -> in the header part of the page.
- ``data`` -> in the data panel on the left of the map.
- ``tool-button`` -> in the tools on the right of the map.
- ``tool-button-separate`` -> in the tools on the right of the map, for the shared button.
- ``tool-<panel-name>`` -> in the tools panel on the right of the map, when the tool is activated.
- ``footer-<panel-name>`` -> in the footer part of the page, when the panel is activated.

Add the following lines in the ``project.yaml`` as ``managed_files``:

.. code:: yaml

  - geoportal/interfaces/desktop_alt\.html\.mako

Create a new WebComponent
-------------------------

In this tutorial we will create a new WebComponent based on `Lit <https://lit.dev/>`_,
and build by `Vite <https://vitejs.dev/>`_.

We will add a button in the tools bar which opens a new tool panel and that can be used to send a feedback.

The tool button should be an instance of
:ngeo_doc:`gmfapi.elements.ToolButtonElement</apidoc/classes/srcapi_elements_ToolButtonElement.default.html>`.

We will directly use
:ngeo_doc:`gmf-tool-button</apidoc/classes/srcapi_elements_ToolButtonElement.ToolButtonDefault.html>`.

And panel should be an instance of:
:ngeo_doc:`gmfapi.elements.ToolPanelElement</apidoc/classes/srcapi_elements_ToolPanelElement.default.html>`.

We will directly get the existing component from the demo.

.. prompt:: bash

   cd /tmp
   git clone git@github.com:camptocamp/demo_geomapfish.git
   cd -
   cp --recursive /tmp/demo_geomapfish/webcomponents \
      /tmp/demo_geomapfish/package.json \
      /tmp/demo_geomapfish/package-lock.json \
      /tmp/demo_geomapfish/tsconfig.json \
      /tmp/demo_geomapfish/vite.config.ts .


Add the following lines in the ``.gitignore``:

.. code::

   /node_modules

.. note::

    The web component file is `custom/webcomponents/feedback.tspy <https://github.com/camptocamp/demo_geomapfish/blob/master/custom/webcomponents/feedback.ts>`_.


Build it in the config image
----------------------------

In the ``Dockerfile`` we will add two stages, one to build the WebComponent and an other just to add the
build artifacts to the config image.

Add the following lines at the end of ``Dockerfile``:

.. code::

   ###############################################################################

   FROM node:16-slim AS custom-build

   WORKDIR /app
   COPY package.json ./

   RUN npm install

   COPY tsconfig.json vite.config.ts ./
   COPY webcomponents/ ./webcomponents/
   RUN npm run build

   ###############################################################################

   FROM gmf_config AS config
   COPY --from=custom-build /app/dist/ /etc/geomapfish/static/custom/

Add the following lines in the ``.dockerignore``:

.. code::

   !webcomponents/
   !package.json
   !package-lock.json
   !tsconfig.json
   !vite.config.ts

Add the following lines in the ``project.yaml`` as ``managed_files``:

.. code:: yaml

  - Dockerfile
  - \.dockerignore


Add it to the interface template
--------------------------------

Then we will include the following HTML in the canvas element, in ``geoportal/interfaces/desktop.html.mako``:

```html
<gmf-tool-button slot="tool-button" iconClasses="fas fa-file-signature" panelName="feedback"></gmf-tool-button>
```

The panel will be included with the following HTML:

```html
<proj-feedback slot="tool-panel-feedback"></proj-feedback>
```

The modifications in the ``vars`` file are:
- Add the JavaScript file as ``gmfCustomJavascriptUrl``.
- Be sure that we have the CSS file as ``gmfCustomStylesheetUrl``.
- Add in comment all the needed configuration to be able to debug.

Apply the following diff in the ``geoportal/vars.yaml``:

.. code:: diff

     vars:
       interfaces_config:
         desktop:
           constants:
   +
   +         # For dev, the corresponding values in static should also be commented.
   +         # gmfCustomJavascriptUrl:
   +         #   - https://localhost:3001/@vite/client
   +         #   - https://localhost:3001/webcomponents/index.ts
   +
   +         # Used in the web component to get the service URL based on `gmfBase`.
   +         sitnFeedbackPath: custom/feedback
   +
   +       static:
   +         # Those two lines should be commented in dev mode.
   +         gmfCustomJavascriptUrl:
   +           name: '/etc/geomapfish/static/custom/custom.es.js'
   +         gmfCustomStylesheetUrl:
   +           name: /etc/geomapfish/static/css/desktop_alt.css
   +
   +       routes:
   +         gmfBase:
   +           name: base

   +   # For dev this line is needed to allow the page to load the files from Vite dev server.
   +   # content_security_policy_main_script_src_extra: "http://localhost:3001"

Debugging Custom JavaScript and service
---------------------------------------

The usual build and run will also work for the custom JavaScript and service.
Build and run as usual:

To have a development environment with auto-reload mode, we will start the Vite dev server
locally on port ``3001``.

We also need to get the file from the Vite dev server, for that we need to do the following modifications
in the ``geoportal/vars.yaml`` (don't commit them):

.. code:: diff

              # For dev, the corresponding values in static should also be removed.
   -          # gmfCustomJavascriptUrl:
   -          #   - https://localhost:3001/@vite/client
   -          #   - https://localhost:3001/webcomponents/index.ts
   +          gmfCustomJavascriptUrl:
   +            - https://localhost:3001/@vite/client
   +            - https://localhost:3001/webcomponents/index.ts


              # Those two lines should be commented in dev mode.
   -          gmfCustomJavascriptUrl:
   -            name: '/etc/geomapfish/static/custom/custom.es.js'
   +          # gmfCustomJavascriptUrl:
   +          #   name: '/etc/geomapfish/static/custom/custom.es.js'


        # For dev this line is needed to allow the page to load the files from Vite dev server.
   -    # content_security_policy_main_script_src_extra: "http://localhost:3001"
   +    content_security_policy_main_script_src_extra: "http://localhost:3001"

Rename the ``docker-compose.override.sample.yaml`` file to ``docker-compose.override.yaml``.

Build and run as usual.

Download and start the Vite dev server:

.. prompt:: bash

   npm install
   npm run dev

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
