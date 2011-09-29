/*
 * @include Ext/src/ext-core/examples/jsonp/jsonp.js
 * @include OpenLayers/Format/GeoJSON.js
 * @include OpenLayers/Layer/Vector.js
 * @include OpenLayers/Renderer/SVG.js
 * @include OpenLayers/Renderer/VML.js
 * @include OpenLayers/Feature/Vector.js
 * @include OpenLayers/Geometry/Point.js
 * @include App/Map.js
 * @include App/globals.js
 */

Ext.namespace('c2cgeoportal');

/**
 * Note to developers: to use Ext.ux.JSONP the
 * ext/src/ext-core/examples/jsonp/jsonp.js script must be
 * loaded in the page.
 */

/**
 * Class: c2cgeoportal.Map
 *
 * Usage example:
 * (code)
<html>
<head>
<script type="text/javascript" src='build/api.js'></script>
<script type='text/javascript'>
    window.onload = function() {
        var map = new c2cgeoportal.Map({
            div: 'map',
            zoom: 10,
            easting: 500000,
            northing: 5800000,
            height: 400,
            width: 600
        });
    };
</script>
</head>
<body>
<div id='map'></div>
</body>
</html>
 * (end)
 */
c2cgeoportal.Map = function(options) {

    // Private

    /**
     * Method: recenterCb
     * The recenter callback function.
     *
     * Parameters:
     * geojson - {String} The GeoJSON string.
     */
    var recenterCb = function(geojson) {
        var format = new OpenLayers.Format.GeoJSON();
        var feature = format.read(geojson, "Feature");
        this.mapPanel.map.zoomToExtent(feature.bounds);
    };

    /**
     * Method: showMarker
     * Add a marker to the map at a specific location.
     *
     * Parameters:
     * vector - {OpenLayers.Layer.Vector} The vector layer.
     * loc - {OpenLayers.LonLat} The location.
     */
    var showMarker = function(vector, loc) {
        var geometry = new OpenLayers.Geometry.Point(loc.lon, loc.lat);
        var feature = new OpenLayers.Feature.Vector(geometry, {}, {
            externalGraphic: OpenLayers.Util.getImagesLocation() + 'marker.png',
            graphicWidth: 21,
            graphicHeight: 25,
            graphicYOffset: -25/2
        });
        vector.addFeatures([feature]);
    };

    // Public

    Ext.apply(this, {

        /**
         * APIProperty: mapPanel
         * {GeoExt.MapPanel} The map panel.
         */
        mapPanel: null,

        /**
         * APIMethod: recenter
         * Center the map on a specific feature.
         *
         * Parameters:
         * fid - {String} The id of the feature.
         */
        recenter: function(fid) {
            var url = 'changeme/' + fid + '.json';
            Ext.ux.JSONP.request(url, {
                callbackKey: "cb",
                params: {
                    no_geom: true
                },
                callback: recenterCb,
                scope: this
            });
        }
    });

    // Main

    App.setGlobals();

    if (options.easting != undefined && options.northing != undefined) {
        var center = new OpenLayers.LonLat(options.easting, options.northing);
    }

    var map = new App.Map(Ext.apply({
        renderTo: options.div,
        center: center,
        style: {
            position: 'relative' // to position tools.mapbar as absolute
        },
        isApi: true
    }, options));


    var vectorLayer = new OpenLayers.Layer.Vector(
        OpenLayers.Util.createUniqueID("c2cgeoportal"), {
            displayInLayerSwitcher: false,
            alwaysInRange: true
    });
    if (options.showMarker) {
        map.mapPanel.map.addLayer(vectorLayer);
        showMarker(vectorLayer, center || map.mapPanel.map.getCenter());
    }

    this.mapPanel = map.mapPanel;
};
