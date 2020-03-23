.. _integrator_pdfreport:

PDF Reporting
=============

c2cgeoportal offers a *pdfreport* webservice that can be used to generate
advanced PDF reports about a given feature.

It is based upon `Mapfish Print version 3 <https://mapfish.github.io/mapfish-print-doc/>`_
and `Jasper Reports <https://community.jaspersoft.com/project/jasperreports-library>`_.

The webservice is called using the following URL schema:
``https://<host><entrypoint>/pdfreport/<layername>/<featureid>``.


Configuration
-------------

The service is configured in the main ``vars.yaml`` file of the project, as shown in the following example:

.. code::

    vars:
        ...
        pdfreport:
            print_url: '{print_url}'
            layer-defaults: &pdfreport-layer-default
                ogcserver: source for image/png
                check_credentials: True
                srs: EPSG:2056
                map:
                    backgroundlayers: [grp_ly_tilegenerierung_landeskarte]
                    imageformat: image/png
            map-defaults: &pdfreport-map-default
                backgroundlayers: []
                imageformat: image/png
                zoomType: extent
                minScale: 1000
                style:
                    fillColor: red
                    fillOpacity: 0.2
                    symbolizers:
                    -   strokeColor: red
                        strokeWidth: 1
                        type: point
                        pointRadius: 10
            layers:
                ly_a020_belastete_standorte_point:
                    <<: *pdfreport-layer-default
                    map:
                        <<: *pdfreport-map-default
                        backgroundlayers:
                            - grp_ly_tilegenerierung_landeskarte
                            - ly_a020_belastete_standorte_point
                        imageformat: image/jpeg
                some_template_with_no_map:
                    <<: *pdfreport-layer-default
                    spec:
                        layout: some_template_name
                        outputFormat: pdf
                        attributes:
                            ids: %(ids)s
                some_template_with_multi_map:
                    <<: *pdfreport-layer-default
                    maps:
                        -   <<: *pdfreport-map-default
                            backgroundlayers:
                                - grp_ly_tilegenerierung_landeskarte
                        -   <<: *pdfreport-map-default
                            backgroundlayers:
                                - ly_a020_belastete_standorte_point
    update_paths:
        - pdfreport


Regarding the configuration parameters,

* ``print_url`` is the local URL of the MapFish Print instance.
* ``defaults`` contains the default values of parameters not provided explicitly for a given layer.
* ``layers`` is an optional per-layer list of settings specific to the listed layers. The entries of the
  list are the layernames provided as argument of the webservice. If a layer is not listed, the default
  parameters above are used.

``defaults`` and ``layers``-specific parameters are:

* ``ogcserver``: the name of OGC server to use.
* ``check_credentials``: boolean, defines whether layer credentials are checked before generating the report.
  Defaults to ``True``.
* ``srs``: projection code (required when showing the map).
* ``spec``: optional template used to build the ``spec`` argument sent to the MapFish Print webapp.
* ``map``: optional, the map configuration.
* ``maps``: optional, a list of map configurations.

The map configuration can contains the following:

* ``backgroundlayers``: string containing a comma-separated list of WMS layers that should be displayed on
  the map. If the current layer must also be displayed, it should be added to the list. Please note that
  layernames must be embedded in double-quotes ("). Defaults to ``""``.
* ``imageformat``: format of the generated map. Defaults to ``image/png``.
* ``zoomType``: The type of zoom, default is ``extent``.
* ``minScale``: The minimum zoom scale, default is ``1000``.
* ``style``: The style used, default is:

  .. code:: yaml

     fillColor: red
     fillOpacity: 0.2
     symbolizers:
     - strokeColor: red
       strokeWidth: 1
       type: point
       pointRadius: 10

The variables are passed to the ``spec`` template using the ``%(<variable name>)s`` syntax:

* ``layername``: name of the layer.
* ``ids``: JSON representation of the features id.
* ``srs``: projection code.
* ``mapserv_url``: URL of the MapServer proxy.
* ``vector_request_url``: URL of the WFS GetFeature request retrieving the feature geometry in GML.

Configuration of the reports
----------------------------

If you use the ``ids`` in an SQL query, you should use ``$X{IN, <column_name>, $P{ids}}``
to avoid SQL injection, `see also the JasperReports documentation <https://jasperreports.sourceforge.net/sample.reference/query/>`_.
