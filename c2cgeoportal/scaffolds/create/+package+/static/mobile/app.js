Ext.application({
    name: 'App',

    viewport: {
        // hide the address bar
        autoMaximize: true
    },

    requires: [
        'Ext.MessageBox',
        'Ext.data.Store',
        'Ext.data.proxy.JsonP',
        'Ext.TitleBar' // required at least for the Picker
    ],

    views: ['Main', 'Layers', 'Search'],
    models: ['Layer', 'Search'],
    controllers: ["Main", "Search"],

    icon: {
        '57': 'resources/icons/Icon.png',
        '72': 'resources/icons/Icon~ipad.png',
        '114': 'resources/icons/Icon@2x.png',
        '144': 'resources/icons/Icon~ipad@2x.png'
    },

    isIconPrecomposed: true,

    startupImage: {
        '320x460': 'resources/startup/320x460.jpg',
        '640x920': 'resources/startup/640x920.png',
        '768x1004': 'resources/startup/768x1004.png',
        '748x1024': 'resources/startup/748x1024.png',
        '1536x2008': 'resources/startup/1536x2008.png',
        '1496x2048': 'resources/startup/1496x2048.png'
    },

    launch: function() {

        // The application launch function is where the map
        // and layers are created.

        var map = new OpenLayers.Map({
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

        // create the main view and set the map into it
        var mainView = Ext.create('App.view.Main');
        mainView.setMap(map);

        // destroy the #appLoadingIndicator element
        Ext.fly('appLoadingIndicator').destroy();

        // now add the main view to the viewport
        Ext.Viewport.add(mainView);
    },

    onUpdated: function() {
        Ext.Msg.confirm(
            "Application Update",
            "This application has just successfully been updated to the latest version. Reload now?",
            function(buttonId) {
                if (buttonId === 'yes') {
                    window.location.reload();
                }
            }
        );
    }
});
