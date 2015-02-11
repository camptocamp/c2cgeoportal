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

The service is configured in the main ``config.yaml.in`` file of the project
as in the following example:

.. code-block:: yaml

    pdfreport:
        print_url: http://localhost:8080/print-c2cgeoportal-${vars:instanceid} 
        default_backgroundlayers: "grp_ly_tilegenerierung_landeskarte"
        default_imageformat: "image/png"
        srs: "EPSG:21781"
        layers: 
            ly_a020_belastete_standorte_point: 
                backgroundlayers: "grp_ly_tilegenerierung_landeskarte,ly_a020_belastete_standorte_point"
                imageformat: "image/jpeg"
        spec_template: <optional spec template>


with the following parameters:

* ``print_url`` is the local URL of the MapFish Print version 3 instance.
* ``default_backgroundlayers`` and ``default_imageformat`` are default values used when the corresponding parameters are not provided for a given layer.
* ``srs`` is the code of the used projection
* ``layers`` is an optional per-layer list of settings specific to the listed layers. The entries of the list are the layernames provided as argument of the webservice. If a layer is not listed, the default parameters above are used.
* ``backgroundlayers`` is a string containing a comma-separated list of WMS layers that should be displayed on the map. If the curent layer must also be displayed, it should be added to the list. Please note that layernames must be embedded in double-quotes (").
* ``spec_template`` is an optional JSON template used to build the ``spec`` argument sent to the MapFish Print webapp.

If no ``spec_template`` is specified, the following template is used:

.. code-block:: json

    {
        "layout": "%(layername)s",
        "outputFormat": "pdf",
        "attributes": {
            "paramID": "%(id)d",
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
* ``srs``: projection code as passed using the ``srs`` parameter in ``config.yaml.in``
* ``mapserv_url``: URL of the MapServer proxy
* ``vector_request_url``: URL of the WFS GetFeature request retrieving the feature geometry in GML
* ``imageformat``: format of the WMS layer
* ``backgroundlayers``: WMS layers to display on the map (including the current layer)

Configuration of the reports
----------------------------

See the `Mapfish Print documentation <http://mapfish.github.io/mapfish-print-doc/>`_.
