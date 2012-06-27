// Here integrator can set up the layers
var App = App || {};

App.map = new OpenLayers.Map({
    theme: null,
    projection: 'EPSG:900913',
    controls: [
        new OpenLayers.Control.TouchNavigation({
            dragPanOptions: {
                interval: 1,
                enableKinetic: true
            }
        }),
        new OpenLayers.Control.Attribution(),
        new OpenLayers.Control.ScaleLine()
    ],
    layers: [
        new OpenLayers.Layer.OSM("OpenStreetMap", null, {
            transitionEffect: 'resize'
        }),
        new OpenLayers.Layer.OSM(
            "Cycle Map",
            [
                "http://a.tile.opencyclemap.org/cycle/${z}/${x}/${y}.png",
                "http://b.tile.opencyclemap.org/cycle/${z}/${x}/${y}.png",
                "http://c.tile.opencyclemap.org/cycle/${z}/${x}/${y}.png"
            ],
            {
                transitionEffect: 'resize'
            }
        ),
        new OpenLayers.Layer.OSM(
            "Transport Map",
            [
                "http://a.tile2.opencyclemap.org/transport/${z}/${x}/${y}.png",
                "http://b.tile2.opencyclemap.org/transport/${z}/${x}/${y}.png",
                "http://c.tile2.opencyclemap.org/transport/${z}/${x}/${y}.png"
            ],
            {
                transitionEffect: 'resize'
            }

        ),
        new OpenLayers.Layer.WMS(
            "Summits",
            "http://www.camptocamp.org/cgi-bin/c2corg_wms",
            {
                allLayers: ['summits', "huts", "sites", "users"],
                layers: ['summits'],
                transparent: true
            },
            {
                singleTile: true,
                ratio: 1
            }
        )
    ]
});
