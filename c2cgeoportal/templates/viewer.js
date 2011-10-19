var app;
Ext.onReady(function() {
    /*
     * Initialize the application.
     */
    App.setGlobals();
    var events = new Ext.util.Observable();

    var WMTS_OPTIONS = {
% if len(tilecache_url) == 0:
        url: "${request.route_url('tilecache', path='')}",
% else:
        url: '${tilecache_url}',
% endif
        style: 'default',
        dimensions: ['TIME'],
        params: {
            'time': '2011'
        },
        matrixSet: 'swissgrild',
        maxExtent: new OpenLayers.Bounds(420000, 30000, 900000, 350000),
        displayInLayerSwitcher: false,
        requestEncoding: 'REST',
        projection: new OpenLayers.Projection("EPSG:21781"),
        units: "m",
        formatSuffix: 'png',
        serverResolutions: [4000,3750,3500,3250,3000,2750,2500,2250,2000,1750,1500,1250,1000,750,650,500,250,100,50,20,10,5,2.5,2,1.5,1,0.5,0.25,0.1,0.05],
        getMatrix: function() {
            return { identifier: OpenLayers.Util.indexOf(this.serverResolutions, this.map.getResolution()) };
        },
        buffer: 0
    }
    var maxExtent = App.restrictedExtent;

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
                xtype: "panel",
                layout: "fit",
                region: "south",
                height: 160,
                split: true,
                collapseMode: "mini",
                hidden: true
            }, {
                layout: "accordion",
                id: "left-panel",
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
                    id: 'layerpanel',
                    layout: "vbox",
                    layoutConfig: {
                        align: "stretch"
                    }
                }]
            }]
        },

        // configuration of all tool plugins for this application
        tools: [{
            ptype: "cgxp_themeselector",
            outputTarget: "layerpanel",
            layerTreeId: "layertree",
            themes: App.themes,
            outputConfig: {
                layout: "fit",
                style: "padding: 3px;"
            }
        }, {
            ptype: "cgxp_layertree",
            id: "layertree",
            outputConfig: {
                header: false,
                flex: 1,
                layout: "fit",
                autoScroll: true,
                themes: App.themes,
                wmsURL: "${request.route_url('mapserverproxy', path='')}",
                defaultThemes: ${default_themes | n}
            },
            outputTarget: "layerpanel"
        }, {
            ptype: "cgxp_querier",
            outputTarget: "left-panel",
            events: events,
            outputConfig: {
                //hidden: App.user ? false : true
            }
        }, {
            ptype: "cgxp_print",
            legendPanelId: "legendPanel",
            featureGridId: "featureGrid",
            outputTarget: "left-panel",
            options: {
                labelAlign: 'top',
                defaults: {
                    anchor:'100%'
                }
            },
            outputConfig: {
                autoFit: true
            }
        }, {
            ptype: "gxp_zoomtoextent",
            actionTarget: "map.tbar",
            closest: true,
% if user:
            extent: ${user.role.jsextent}
% else:
            extent: ${default_initial_extent | n}
% endif
        }, {
            ptype: "cgxp_zoom",
            actionTarget: "map.tbar",
            toggleGroup: "maptools"
        }, {
            ptype: "gxp_navigationhistory",
            actionTarget: "map.tbar"
        /*
        }, {
            ptype: "cgxp_permalink",
            actionTarget: "map.tbar"
        */
        }, {
            ptype: "gxp_measure",
            actionTarget: "map.tbar",
            toggleGroup: "maptools"
        }, {
            ptype: "cgxp_wmsgetfeatureinfo",
            featureManager: "featuremanager",
            actionTarget: "map.tbar",
            toggleGroup: "maptools",
            events: events
        /*
        }, {
            ptype: "cgxp_fulltextsearch",
            actionTarget: "map.tbar"
        */
        }, {
            ptype: "cgxp_menushortcut",
            type: '->'
        }, {
            ptype: "cgxp_redlining",
            toggleGroup: "maptools",
            actionTarget: "map.tbar"
        }, {
            ptype: "cgxp_legend",
            id: "legendPanel",
            toggleGroup: "maptools",
            actionTarget: "map.tbar"
        }, {
            ptype: "cgxp_menushortcut",
            type: '-'
        }, {
            ptype: "cgxp_login",
            actionTarget: "map.tbar",
            toggleGroup: "maptools",
% if user:
            username: "${user.username}",
% endif
            loginURL: "${request.route_url('login', path='')}",
            logoutURL: "${request.route_url('logout', path='')}"
        }, {
            ptype: "cgxp_menushortcut",
            type: '-'
        },{
            ptype: "cgxp_help",
            url: "#help-url",
            actionTarget: "map.tbar"
        /*
        }, {
            // shared FeatureManager for feature editing, grid and querying
            ptype: "cgxp_featuremanager",
            id: "featuremanager"
*/        }, {
            ptype: "cgxp_featuregrid",
            id: "featureGrid",
            featureManager: "featuremanager",
            outputTarget: "featuregrid-container",
            events: events
        }, {
            ptype: "cgxp_mapopacityslider"
        }],

        // layer sources
        sources: {
            "olsource": {
                ptype: "gxp_olsource",
            }
        },

        // map and layers
        map: {
            id: "app-map", // id needed to reference map in portalConfig above
            projection: "EPSG:21781",
            maxExtent: maxExtent,
            restrictedExtent: maxExtent,
            units: "m",
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
                // Static image version
                /*
                return new OpenLayers.Control.OverviewMap({
                    size: new OpenLayers.Size(200, 100),
                    layers: [new OpenLayers.Layer.Image(
                        OpenLayers.Util.createUniqueID("c2cgeoportal"),
                        "/proj/images/overviewmap.png",
                        OpenLayers.Bounds.fromArray([630000, 238000, 678000, 262000]),
                        new OpenLayers.Size([200, 100]),
                        {isBaseLayer: true}
                    )],
                    mapOptions: {
                        numZoomLevels: 1
                    }
                })*/
                // OSM version
                new OpenLayers.Control.OverviewMap({
                    size: new OpenLayers.Size(200, 100),
                    minRatio: 64, 
                    maxRatio: 64, 
                    layers: [new OpenLayers.Layer.OSM("OSM", [
                            'http://a.tile.openstreetmap.org/${"${z}"}/${"${x}"}/${"${y}"}.png',
                            'http://b.tile.openstreetmap.org/${"${z}"}/${"${x}"}/${"${y}"}.png',
                            'http://c.tile.openstreetmap.org/${"${z}"}/${"${x}"}/${"${y}"}.png'
                        ], {
                            transitionEffect: 'resize',
                            attribution: [
                                "(c) <a href='http://openstreetmap.org/'>OSM</a>",
                                "<a href='http://creativecommons.org/licenses/by-sa/2.0/'>by-sa</a>"
                            ].join(' ')
                        }
                    )]
                })
            ],
            layers: [{
                source: "olsource",
                type: "OpenLayers.Layer.WMTS",
                args: [Ext.applyIf({
                    name: OpenLayers.i18n('ortho'),
                    ref: 'ortho',
                    layer: 'ortho',
                    formatSuffix: 'jpeg',
                    opacity: 0
                }, WMTS_OPTIONS)]
            }, {
                source: "olsource",
                type: "OpenLayers.Layer.WMTS",
                group: 'background',
                args: [Ext.applyIf({
                    name: OpenLayers.i18n('plan'),
                    ref: 'plan',
                    layer: 'plan',
                    group: 'background'
                }, WMTS_OPTIONS)]
            }, {
                source: "olsource",
                type: "OpenLayers.Layer.WMTS",
                group: 'background',
                args: [Ext.applyIf({
                    name: OpenLayers.i18n('plan color'),
                    ref: 'plan_color',
                    layer: 'plan_color',
                    group: 'background'
                }, WMTS_OPTIONS)]
            }, {
                source: "olsource",
                type: "OpenLayers.Layer",
                group: 'background',
                args: [OpenLayers.i18n('blank'), {
                    displayInLayerSwitcher: false,
                    ref: 'blank',
                    group: 'background'
                }]
            }],
            items: []
        }
    });

    // remove loading message
    // FIXME: really works?
    Ext.get('loading').remove();
    Ext.fly('loading-mask').fadeOut({
        remove:true
    });
});
