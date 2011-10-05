var app;
Ext.onReady(function() {
    /*
     * Initialize the application.
     */
    App.setGlobals();

    var maxExtent = OpenLayers.Bounds.fromArray(App.restrictedExtent);
    app = new gxp.Viewer({
        portalConfig: {
            layout: "border",
            // by configuring items here, we don't need to configure portalItems
            // and save a wrapping container
            items: [{
                region: "north",
                contentEl: 'header-out'
            },
            "app-map",
            {
                id: "featuregrid-container",
                xtype: "container",
                layout: "fit",
                region: "south",
                height: 160,
                split: true,
                collapseMode: "mini"
            }, {
                layout: "accordion",
                region: "west",
                width: 300,
                minWidth: 300,
                split: true,
                collapseMode: "mini",
                border: false,
                defaults: {width: 300},
                items: [{
                    xtype: "panel",
                    title: OpenLayers.i18n("layertree"),
                    layout: "vbox",
                    layoutConfig: {
                        align: "stretch"
                    },
                    items: [{
                        id: "themeselector-container",
                        xtype: "container",
                        layout: "fit",
                        style: "padding: 3px;"
                    }, {
                        id: "layertree-container",
                        xtype: "container",
                        layout: "fit"
                    }]
                }, {
                    id: "querier-container",
                    xtype: "panel",
                    layout: "fit"
                }, {
                    id: "print-container",
                    xtype: "panel",
                    layout: "fit"
                }]
            }]
        },

        // configuration of all tool plugins for this application
        tools: [{
            ptype: "cgxp_themeselector",
            outputTarget: "themeselector-container",
            themes: App.themes,
            tree: {}//layerTreePanel // TODO
        /*
        }, {
            ptype: "cgxp_layertree",
            outputConfig: {
                header: false,
                flex: 1,
                autoScroll: true
            },
            outputTarget: "layertree-container"
        }, {
            ptype: "cgxp_querier",
            outputTarget: "querier-container"
        }, {
            ptype: "cgxp_print",
            outputTarget: "print-container"
        */
        }, {
            ptype: "gxp_zoomtoextent",
            actionTarget: "map.tbar"
        /*
        }, {
            ptype: "cgxp_zoomin",
            actionTarget: "map.tbar",
            toggleGroup: "maptools"
        }, {
            ptype: "cgxp_zoomout",
            actionTarget: "map.tbar"
        */
        }, {
            ptype: "gxp_navigationhistory",
            actionTarget: "map.tbar"
        /*
        }, {
            ptype: "cgxp_permalink",
            actionTarget: "map.tbar"
        }, {
            ptype: "cgxp_measure",
            actionTarget: "map.tbar",
            toggleGroup: "maptools"
        }, {
            ptype: "cgxp_wmsgetfeatureinfo",
            featureManager: "featuremanager",
            actionTarget: "map.tbar",
            toggleGroup: "maptools"
        }, {
            ptype: "cgxp_fulltextsearch",
            actionTarget: "map.tbar"
        }, {
            ptype: "cgxp_legend",
            actionTarget: "map.tbar"
        }, {
            ptype: "cgxp_loginform",
            actionTarget: "map.tbar"
        }, {
            ptype: "cgxp_help",
            url: "#help-url",
            actionTarget: "map.tbar"
        }, {
            ptype: "cgxp_redlining",
            actionTarget: "map.tbar"
        }, {
            // shared FeatureManager for feature editing, grid and querying
            ptype: "cgxp_featuremanager",
            id: "featuremanager"
        }, {
            ptype: "cgxp_featuregrid",
            featureManager: "featuremanager",
            outputTarget: "featuregrid-container"
        */
        }],

        // layer sources
        defaultSourceType: "gxp_wmssource",
        sources: {
            // TODO: configure sources
            /*
            local: {
                url: "/geoserver/wms",
                version: "1.1.1"
            },
            google: {
                ptype: "gxp_googlesource"
            }
            */
        },

        // map and layers
        map: {
            id: "app-map", // id needed to reference map in portalConfig above
            projection: "EPSG:21781",
            maxExtent: maxExtent,
            restrictedExtent: maxExtent,
            units: "m",
            theme: null, // or OpenLayers will attempt to load it default theme
            resolutions: [4000,2000,1000,500,250,100,50,20,10,5,2.5,1,0.5,0.25,0.1,0.05],
            controls: [
                new OpenLayers.Control.Navigation(),
                new OpenLayers.Control.KeyboardDefaults(),
                new OpenLayers.Control.PanZoomBar({panIcons: false}),
                new OpenLayers.Control.ArgParser(),
                new OpenLayers.Control.Attribution(),
                new OpenLayers.Control.ScaleLine({
                    bottomInUnits: false,
                    bottomOutUnits: false
                }),
                new OpenLayers.Control.MousePosition({numDigits: 0}),
                App.createOverviewMap(maxExtent)
            ],
            // TODO: configure layers
            layers: [
                /*
            {
                source: "google",
                name: "TERRAIN",
                group: "background"
            }, {
                source: "local",
                name: "usa:states",
                selected: true
            }
                */
            ],
            items: [/*{
                xtype: "cgxp_opacityslider"
            }*/]
        }
    });

    // remove loading message
    Ext.get('loading').remove();
    Ext.fly('loading-mask').fadeOut({
        remove:true
    });
});
