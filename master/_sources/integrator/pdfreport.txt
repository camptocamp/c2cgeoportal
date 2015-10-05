.. _integrator_pdfreport:

PDF Reporting
=============

c2cgeoportal offers a *pdfreport* webservice that can be used to generate
advanced PDF reports about a given feature.

It is based upon `MapfishPrint version 3 <http://mapfish.github.io/mapfish-print-doc/>`_
and `Jasper Reports <http://community.jaspersoft.com/project/jasperreports-library>`_.

The webservice is called using the following URL schema:
``http://<host>/<instanceid>/wsgi/pdfreport/<layername>/<featureid>``.


Configuration
-------------

The service is configured in the main ``vars_<package>.yaml`` file of the project
as in the following example:

.. code-block:: yaml

    vars:
        ...
        pdfreport:
            defaults:
                check_credentials: False
                srs: EPSG:21781
                map:
                    backgroundlayers: [grp_ly_tilegenerierung_landeskarte]
                    imageformat: image/png
            layers:
                ly_a020_belastete_standorte_point:
                    map:
                        backgroundlayers:
                            - grp_ly_tilegenerierung_landeskarte
                            - ly_a020_belastete_standorte_point
                        imageformat: image/jpeg
                some_template_with_no_map:
                    spec:
                        layout: some_template_name
                        outputFormat: pdf
                        attributes:
                            paramID: "%(id)s"
                some_template_with_multi_map:
                    maps:
                        - backgroundlayers:
                            - grp_ly_tilegenerierung_landeskarte
                        - backgroundlayers:
                            - ly_a020_belastete_standorte_point
    update_paths:
        - pdfreport


with the following parameters:

* ``print_url`` is the local URL of the MapFish Print version 3 instance.
* ``defaults`` contains the default values of parameters not provided explicitely for a given layer.
* ``layers`` is an optional per-layer list of settings specific to the listed layers. The entries of the list are the layernames provided as argument of the webservice. If a layer is not listed, the default parameters above are used.

``defaults`` and ``layers``-specific parameters are:

* ``check_credentials``: boolean, wether layer credentials are checked before generating the report. Defaults to ``True``.
* ``srs``: projection code (required when showing the map).
* ``backgroundlayers``: string containing a comma-separated list of WMS layers that should be displayed on the map. If the curent layer must also be displayed, it should be added to the list. Please note that layernames must be embedded in double-quotes ("). Defaults to ``""``.
* ``imageformat``: format of the generated map. Defaults to ``image/png``.
* ``spec_template``: optional JSON template used to build the ``spec`` argument sent to the MapFish Print webapp.

If no ``spec_template`` is provided, the following template is used:

.. code-block:: json

    {
        "layout": "%(layername)s",
        "outputFormat": "pdf",
        "attributes": {
            "paramID": "%(id)s",
            "map": {
                "projection": "%(srs)s",
                "dpi": 254,
                "rotation": 0,
                "bbox": [0, 0, 1000000, 1000000],
                "zoomToFeatures": {
                    "zoomType": "center",
                    "layer": "vector",
                    "minScale": 25000
                },
                "layers": [{
                    "type": "gml",
                    "name": "vector",
                    "style": {
                        "version": "2",
                        "[1 > 0]": {
                            "fillColor": "red",
                            "fillOpacity": 0.2,
                            "symbolizers": [{
                                "strokeColor": "red",
                                "strokeWidth": 1,
                                "type": "point",
                                "pointRadius": 10
                            }]
                        }
                    },
                    "opacity": 1,
                    "url": "%(vector_request_url)s"
                }, {
                    "baseURL": "%(mapserv_url)s",
                    "opacity": 1,
                    "type": "WMS",
                    "serverType": "mapserver",
                    "layers": ["%(backgroundlayers)s"],
                    "imageFormat": "%(imageformat)s"
                }]
            }
        }
    }

Variables may be inserted using the ``%(<variable name>)s`` syntax. The following
variables values are passed to the template:

* ``layername``: name of the layer
* ``id``: feature id
* ``srs``: projection code
* ``mapserv_url``: URL of the MapServer proxy
* ``vector_request_url``: URL of the WFS GetFeature request retrieving the feature geometry in GML
* ``imageformat``: format of the WMS layer
* ``backgroundlayers``: WMS layers to display on the map (including the current layer)

Configuration of the reports
----------------------------

See the `Mapfish Print documentation <http://mapfish.github.io/mapfish-print-doc/>`_.
