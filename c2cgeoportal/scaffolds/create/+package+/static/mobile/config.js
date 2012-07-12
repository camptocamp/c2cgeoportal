/*
 * This file represents the customization point for the application integrator.
 *
 * After execution of this script an OpenLayers map filled with layers should
 * be available in App.map.
 *
 * This file also contains translations for the application strings.
 */

OpenLayers.Lang.en = {
    "summits": "Summits",
    "huts": "Huts",
    "sites": "Sites",
    "users": "Users"
};
OpenLayers.Lang.fr = {
    "summits": "Sommets",
    "huts": "Cabanes",
    "sites": "Sites",
    "users": "Utilisateurs"
};
OpenLayers.Lang.setCode("${lang}");

// define the map and layers
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
                "http://a.tile.opencyclemap.org/cycle/${'${z}/${x}/${y}'}.png",
                "http://b.tile.opencyclemap.org/cycle/${'${z}/${x}/${y}'}.png",
                "http://c.tile.opencyclemap.org/cycle/${'${z}/${x}/${y}'}.png"
            ],
            {
                transitionEffect: 'resize'
            }
        ),
        new OpenLayers.Layer.OSM(
            "Transport Map",
            [
                "http://a.tile2.opencyclemap.org/transport/${'${z}/${x}/${y}'}.png",
                "http://b.tile2.opencyclemap.org/transport/${'${z}/${x}/${y}'}.png",
                "http://c.tile2.opencyclemap.org/transport/${'${z}/${x}/${y'}}.png"
            ],
            {
                transitionEffect: 'resize'
            }

        ),
        new OpenLayers.Layer.WMS(
            "Summits",
            "http://www.camptocamp.org/cgi-bin/c2corg_wms",
            {
                layers: ['summits'],
                transparent: true
            },
            {
                allLayers: ['summits', "huts", "sites", "users"],
                singleTile: true,
                ratio: 1
            }
        )
    ]
});
