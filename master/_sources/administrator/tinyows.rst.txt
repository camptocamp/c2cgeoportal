.. _administrator_tinyows:

WFS-T with TinyOWS
==================
Based on `TinyOWS <http://mapserver.org/tinyows/>`__ c2cgeoportal layers can be
edited via WFS-T, for example using QGIS as a client. c2cgeoportal acts as a
proxy to TinyOWS to limit access to authorized users.

The following explains how to configure WFS-T for a c2cgeoportal layer.

Apache configuration for TinyOWS
---------------------------------

When creating a c2cgeoportal project using the :ref:`Paste skeletons <integrator_create_application>`
there will already be a default Apache configuration file for TinyOWS under the
location ``apache/tinyows.conf.mako``. Uncomment the lines in this file to
enable TinyOWS::

    ScriptAlias /${instanceid}/tinyows /usr/lib/cgi-bin/tinyows
    <Location /${instanceid}/tinyows>
      SetEnv TINYOWS_CONFIG_FILE ${directory}/mapserver/tinyows.xml

      # restrict access to localhost so that all requests go through the proxy
      Options All
      Order deny,allow
      Deny from all
      Allow from 127.0.0.1 ::1
    </Location>

Make sure that the location of TinyOWS (``/usr/lib/cgi-bin/tinyows``) matches
your installation. The configuration restricts the access to TinyOWS to
``localhost`` so that all external requests go through the TinyOWS proxy of
c2cgeoportal.

TinyOWS configuration
---------------------

The configuration of TinyOWS is made in a XML file, which is located at
``mapserver/tinyows.xml.mako``::

    <tinyows
        online_resource="http://${host}/${instanceid}/wsgi/tinyows_proxy"
        schema_dir="/usr/share/tinyows/schema/"
        log="tinyows.log"
        log_level="1"
        check_schema="0">

      <contact
          name="GeoMapFish"
          site="http://www.geomapfish.org/"
          email="geomapfish@googlegroups.com" />

      <metadata
          name="GeoMapFish TinyOWS Server"
          title="GeoMapFish TinyOWS Server" />

      <pg
          host="${dbhost}"
          user="${dbuser}"
          password="${dbpassword}"
          port="${dbport}"
          dbname="${db}" />

      <layer
          retrievable="1"
          writable="1"
          ns_prefix="tows"
          ns_uri="http://www.tinyows.org/"
          name="point"
          schema="edit"
          table="point"
          title="Points"
          pkey="id" />
    </tinyows>

In the root element ``tinyows`` the following properties have to be set:

1. ``online_resource`` - This should be the URL to the TinyOWS proxy, usually
   ``http://${host}/${instanceid}/wsgi/tinyows_proxy``.
2. ``schema_dir`` - The path to the TinyOWS schema directory. Adapt this path
   according to your installation.
3. ``log`` - Path to the TinyOWS log file. This file must be writable.
4. ``log_level`` - The log level (default: 1). Please refer to the
   `TinyOWS documentation <http://mapserver.org/tinyows/configfile.html#tinyows-element>`__
   for more information.
5. ``check_schema`` - If the input data is validated against the schema when
   creating new features. In a vhost environment the schema check has to be
   disabled, so that the proxy can function properly. This does not disable
   the validation database-side though!

The database connection is configured in the element ``pg``. By default the
same database as for the c2cgeoportal application will be used.

The layers that should be accessible with TinyOWS have to specified with
``layer`` elements::

      <layer
          retrievable="1"
          writable="1"
          ns_prefix="tows"
          ns_uri="http://www.tinyows.org/"
          name="point"
          schema="edit"
          table="point"
          title="Points"
          pkey="id" />

In this example a layer named ``point`` is created for table ``point`` in the
database schema ``edit`` with the primary key column ``id``. This layer is both
``retrievable`` and ``writable``.

The referenced database table must contain a single geometry column and must
provide a sequence for the primary key so that new entities can be created.

The layer's name must match the name of a c2cgeoportal layer. This c2cgeoportal
layer must be assigned to a restriction-area  whose``readwrite`` flag is
enabled. The restriction-area will be used inside the proxy to restrict the
access to a layer to the users of a restriction-area.

.. warning::

    The actual *area* of a restriction-area is ignored in the TinyOWS proxy.
    The proxy only checks for authorized users. To limit the access to a
    specific area, the ``geobbox`` property has to be set for a layer in the
    TinyOWS XML configuration. Please refer to the
    `TinyOWS documentation <http://mapserver.org/tinyows/configfile.html#layer-element>`__
    for more information.

After the configuration is made, re-build the c2cgeoportal application::

    make <profile>.mk build

Editing a layer with WFS-T
--------------------------

The configured layers can now be edited using your favorite GIS supporting
WFS-T. For example in QGIS add a new WFS layer with the URL
``http://${host}/${instanceid}/wsgi/tinyows_proxy`` (e.g.
``http://geomapfish.demo-camptocamp.com/demo/wsgi/tinyows_proxy``). For the
authentication use your c2cgeoportal account details.
