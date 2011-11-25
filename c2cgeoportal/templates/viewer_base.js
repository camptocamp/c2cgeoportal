    /*
     * Initialize the application.
     */
    // OpenLayers
    <%block name="init_openlayers">\
    OpenLayers.Number.thousandsSeparator = ' ';
    OpenLayers.IMAGE_RELOAD_ATTEMPTS = 5;
    OpenLayers.DOTS_PER_INCH = 72;
    </%block>\

    // Ext
    <%block name="init_ext">\
    Ext.QuickTips.init();
    </%block>\

    <%block name="init_project">\
    OpenLayers.ImgPath = 'to be overwritten';
    Ext.BLANK_IMAGE_URL = 'to be overwritten';
    </%block>\

    // Apply same language than on the server side
    OpenLayers.Lang.setCode("${lang}");

    // Themes definitions
    /* errors (if any): ${themesError | n} */
    var THEMES = {
        "local": ${themes | n}
    % if external_themes:
        , "external": ${external_themes | n}
    % endif
    };

    <%block name="initial_extent">\
% if user:
    var INITIAL_EXTENT = ${user.role.jsextent};
% else:
    <%block name="default_initial_extent">\
    var INITIAL_EXTENT = [420000, 30000, 900000, 350000];
    </%block>\
% endif
    </%block>\

    <%block name="restricted_extent">\
    var RESTRICTED_EXTENT = [420000, 30000, 900000, 350000];
    </%block>\

    // Used to transmit event throw the application
    var EVENTS = new Ext.util.Observable();

    <%block name="wmts_options">\
    var WMTS_OPTIONS = {
% if len(tilecache_url) == 0:
        url: "${request.route_url('tilecache', path='')}",
% else:
        url: '${tilecache_url}',
% endif
        displayInLayerSwitcher: false,
        requestEncoding: 'REST',
        buffer: 0,
        <%block name="wmts_options_settings">\
        style: 'default',
        dimensions: ['TIME'],
        params: {
            'time': '2011'
        },
        matrixSet: 'swissgrid',
        maxExtent: new OpenLayers.Bounds(420000, 30000, 900000, 350000),
        projection: new OpenLayers.Projection("EPSG:21781"),
        units: "m",
        formatSuffix: 'png',
        serverResolutions: [4000,3750,3500,3250,3000,2750,2500,2250,2000,1750,1500,1250,1000,750,650,500,250,100,50,20,10,5,2.5,2,1.5,1,0.5,0.25,0.1,0.05],
        </%block>\
        getMatrix: function() {
            return { identifier: OpenLayers.Util.indexOf(this.serverResolutions, this.map.getResolution()) };
        }
    };
    </%block>\

    <%block name="viewer">\
    app = new gxp.Viewer({
        portalConfig: {
            <%block name="viewer_portal_config">\
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
                hidden: true,
                bodyStyle: 'background-color: transparent;'
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
            </%block>\
        },

        // configuration of all tool plugins for this application
        tools: [
        <%block name="viewer_tools">\
        <%block name="viewer_tools_disclaimer">\
        {
            ptype: "cgxp_disclaimer",
            outputTarget: "map"
        },
        </%block>\
        <%block name="viewer_tools_themeselector">\
        {
            ptype: "cgxp_themeselector",
            outputTarget: "layerpanel",
            layerTreeId: "layertree",
            themes: THEMES,
            outputConfig: {
                layout: "fit",
                style: "padding: 3px;"
            }
        }, 
        </%block>\
        <%block name="viewer_tools_layertree">\
        {
            ptype: "cgxp_layertree",
            id: "layertree",
            outputConfig: {
                header: false,
                flex: 1,
                layout: "fit",
                autoScroll: true,
                themes: THEMES,
                <%block name="viewer_tools_layertree_options">\
                defaultThemes: ["default theme"],
                </%block>\
                wmsURL: "${request.route_url('mapserverproxy', path='')}"
            },
            outputTarget: "layerpanel"
        }, 
        </%block>\
        <%block name="viewer_tools_querier">\
        {
            ptype: "cgxp_querier",
            outputTarget: "left-panel",
            events: EVENTS,
            mapserverproxyURL: "${request.route_url('mapserverproxy', path='')}",
            // don't work with actual version of mapserver, the proxy will limit to 200
            // it is intended to be reactivated this once mapserver is fixed
            //maxFeatures: 200,
            <%block name="viewer_tools_querier_options">\
            srsName: 'EPSG:21781',
            featureType: "query_layer",
            </%block>\
            outputConfig: {
% if not user:
                hidden: true
% endif
            }
        }, 
        </%block>\
        <%block name="viewer_tools_print">\
        {
            ptype: "cgxp_print",
            legendPanelId: "legendPanel",
            featureGridId: "featureGrid",
            outputTarget: "left-panel",
            printURL: "${request.route_url('printproxy', path='')}",
            mapserverURL: "${request.route_url('mapserverproxy', path='')}", 
            options: {
                labelAlign: 'top',
                defaults: {
                    anchor:'100%'
                }
            },
            outputConfig: {
                autoFit: true
            }
        }, 
        </%block>\
        <%block name="viewer_tools_featuregrid">\
        {
            ptype: "cgxp_featuregrid",
            id: "featureGrid",
            featureManager: "featuremanager",
            csvURL: "${request.route_url('csvecho')}",
            maxFeatures: 200,
            outputTarget: "featuregrid-container",
            events: EVENTS
        }, 
        </%block>\
        <%block name="viewer_tools_mapopacityslider">\
        {
            ptype: "cgxp_mapopacityslider"
        },
        </%block>\
        <%block name="viewer_tools_additional">\
        </%block>\
        <%block name="viewer_tools_toolbar">\
        {
            ptype: "gxp_zoomtoextent",
            actionTarget: "map.tbar",
            closest: true,
            extent: INITIAL_EXTENT
        }, {
            ptype: "cgxp_zoom",
            actionTarget: "map.tbar",
            toggleGroup: "maptools"
        }, {
            ptype: "gxp_navigationhistory",
            actionTarget: "map.tbar"
        }, 
        <%block name="viewer_tools_toolbar_permalink">\
        {
            ptype: "cgxp_permalink",
            actionTarget: "map.tbar"
        }, 
        </%block>\
        {
            ptype: "cgxp_measure",
            actionTarget: "map.tbar",
            toggleGroup: "maptools"
        }, 
        <%block name="viewer_tools_toolbar_getfeatureinfo">\
        {
            ptype: "cgxp_wmsgetfeatureinfo",
            featureManager: "featuremanager",
            actionTarget: "map.tbar",
            toggleGroup: "maptools",
            events: EVENTS
        }, 
        </%block>\
        <%block name="viewer_tools_fulltextsearch">\
        {
            ptype: "cgxp_fulltextsearch",
            url: "${request.route_url('fulltextsearch', path='')}",
            actionTarget: "map.tbar"
        },
        </%block>\
        {
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
        }, 
        <%block name="viewer_tools_toolbar_login">\
        {
            ptype: "cgxp_login",
            actionTarget: "map.tbar",
            toggleGroup: "maptools",
% if user:
            username: "${user.username}",
% endif
            loginURL: "${request.route_url('login', path='')}",
            logoutURL: "${request.route_url('logout', path='')}"
        },{
            ptype: "cgxp_menushortcut",
            type: '-'
        }, 
        </%block>\
        {
            ptype: "cgxp_help",
            <%block name="viewer_tools_toolbar_helpurl">\
            url: "#help-url",
            </%block>\
            actionTarget: "map.tbar"
        /*
        }, {
            // shared FeatureManager for feature editing, grid and querying
            ptype: "cgxp_featuremanager",
            id: "featuremanager"
*/        }
        </%block>\
        </%block>\
        ],

        // layer sources
        sources: {
            <%block name="viewer_sources">\
            "olsource": {
                ptype: "gxp_olsource"
            }
            </%block>\
        },

        // map and layers
        map: {
            <%block name="viewer_map">\
            <%block name="viewer_map_id">\
            id: "app-map", // id needed to reference map in portalConfig above
            </%block>\
            xtype: 'cgxp_mappanel',
            projection: "EPSG:21781",
            extent: INITIAL_EXTENT,
            maxExtent: RESTRICTED_EXTENT,
            restrictedExtent: RESTRICTED_EXTENT,
            stateId: "map",
            <%block name="viewer_map_options">\
            units: "m",
            resolutions: [4000,2000,1000,500,250,100,50,20,10,5,2.5,1,0.5,0.25,0.1,0.05],
            </%block>\
            controls: [
                <%block name="viewer_controls">\
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
                <%block name="viewer_add_controls">\
                // OSM version
                new OpenLayers.Control.OverviewMap({
                    size: new OpenLayers.Size(200, 100),
                    minRatio: 64, 
                    maxRatio: 64, 
                    mapOptions: {
                        theme: null
                    },
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
                </%block>\
                </%block>\
            ],
            layers: [
            <%block name="viewer_layers">\
            {
                source: "olsource",
                type: "OpenLayers.Layer.WMTS",
                args: [Ext.applyIf({
                    name: OpenLayers.i18n('ortho'),
                    mapserverLayers: 'ortho',
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
                    mapserverLayers: 'plan',
                    ref: 'plan',
                    layer: 'plan',
                    group: 'background'
                }, WMTS_OPTIONS)]
            }, 
            {
                source: "olsource",
                type: "OpenLayers.Layer",
                group: 'background',
                args: [OpenLayers.i18n('blank'), {
                    displayInLayerSwitcher: false,
                    ref: 'blank',
                    group: 'background'
                }]
            }
            </%block>\
            ],
            items: []
        }
        </%block>\
    });
    </%block>\

    app.on('ready', function() {
    <%block name="viewer_ready">\
        // remove loading message
        Ext.get('loading').remove();
        Ext.fly('loading-mask').fadeOut({
            remove: true
        });
    </%block>\
    }, app);
