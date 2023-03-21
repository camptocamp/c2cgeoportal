.. _administrator_tinyows:

Transactional WFS with TinyOWS
==============================

Based on `TinyOWS <https://mapserver.org/tinyows/>`_, c2cgeoportal mapserver layers can be
edited via Transactional WFS (WFS-T), for example using QGIS as a client. c2cgeoportal acts as a
proxy to TinyOWS to limit access to authorized users.

.. note::

   This is not needed for QGIS server, because it natively supports Transactional WFS.

The following explains how to configure WFS-T for a c2cgeoportal layer.

TinyOWS configuration
---------------------

The configuration of TinyOWS is made in an XML file, which is located at
``mapserver/tinyows.xml.tmpl``:

.. code:: xml

    <tinyows
        online_resource="https://${VISIBLE_WEB_HOST}/tinyows_proxy"
        schema_dir="/usr/share/tinyows/schema/"
        log_level="1"
        check_schema="0">

      <contact
          name="GeoMapFish"
          site="https://www.geomapfish.org/"
          email="geomapfish@googlegroups.com" />

      <metadata
          name="GeoMapFish TinyOWS Server"
          title="GeoMapFish TinyOWS Server" />

      <pg
          host="${PGHOST}"
          user="${PGUSER}"
          password="${PGPASSWORD}"
          port="${PGPORT}"
          dbname="${PGDATABASE}" />

      <layer
          retrievable="1"
          writable="1"
          ns_prefix="tows"
          ns_uri="https://www.tinyows.org/"
          name="point"
          schema="edit"
          table="point"
          title="Points"
          pkey="id" />
    </tinyows>

In the root element ``tinyows``, the following properties have to be set:

* ``online_resource`` - This should be the URL to the TinyOWS proxy, usually
  ``https://${VISIBLE_WEB_HOST}/tinyows_proxy``.
* ``schema_dir`` - The path to the TinyOWS schema directory. Adapt this path according to your installation.
* ``log_level`` - The log level (default: 1). Please refer to the
  `TinyOWS documentation <https://mapserver.org/tinyows/configfile.html#tinyows-element>`__
  for more information.
* ``check_schema`` - Defines if the input data is validated against the schema when new features are
  created. In a vhost environment, the schema check has to be disabled so that the proxy can function
  properly. This does not disable the validation database-side though!

The database connection is configured in the element ``pg``. By default, the
same database as for the c2cgeoportal application will be used.

The layers that should be accessible with TinyOWS have to specified with ``layer`` elements:

.. code:: xml

      <layer
          retrievable="1"
          writable="1"
          ns_prefix="tows"
          ns_uri="https://www.tinyows.org/"
          name="point"
          schema="edit"
          table="point"
          title="Points"
          pkey="id" />

In this example, a layer named ``point`` is created for the table ``point`` in the
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
    `TinyOWS documentation <https://mapserver.org/tinyows/configfile.html#layer-element>`__
    for more information.

After the configuration is made, re-build your c2cgeoportal application as usual.


Editing a layer with WFS-T
--------------------------

The configured layers can now be edited using your favorite GIS supporting
WFS-T. For example, in QGIS, add a new WFS layer with the URL
``https://${host}/tinyows_proxy`` (e.g.
``https://geomapfish.demo-camptocamp.com/demo/tinyows_proxy``). For the
authentication use your c2cgeoportal account details.
