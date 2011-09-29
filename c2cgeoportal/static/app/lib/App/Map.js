/*
 * @include OpenLayers/Projection.js
 * @include OpenLayers/Map.js
 * @include OpenLayers/Layer/WMS.js
 * @include OpenLayers/Layer/WMTS.js
 * @include OpenLayers/Layer/TileCache.js
 * @include OpenLayers/Control/Navigation.js
 * @include OpenLayers/Control/KeyboardDefaults.js
 * @include OpenLayers/Control/PanZoomBar.js
 * @include OpenLayers/Control/ArgParser.js
 * @include OpenLayers/Control/Attribution.js
 * @include OpenLayers/Control/ScaleLine.js
 * @include OpenLayers/Control/OverviewMap.js
 * @include OpenLayers/Control/MousePosition.js
 * @include OpenLayers/Layer/Vector.js
 * @include OpenLayers/Layer/Image.js
 * @include OpenLayers/Layer/XYZ.js
 * @include OpenLayers/Renderer/SVG.js
 * @include OpenLayers/Renderer/VML.js
 * @include OpenLayers/Format/WMSCapabilities.js
 * @include OpenLayers/Format/WMSCapabilities/v1_1_1.js
 * @include GeoExt/widgets/MapPanel.js
 * @include GeoExt/data/LayerStore.js
 * @include Ext/src/ext-core/examples/jsonp/jsonp.js
 * @include App/Tools.js
 */

Ext.namespace('App');

/**
 * Constructor: App.Map
 * Creates a {GeoExt.MapPanel} internally. Use the "mapPanel" property
 * to get a reference to the map panel.
 *
 * Parameters:
 * options - {Object} Options passed to the {GeoExt.MapPanel}.
 * events - {Ext.util.Observable} The application events manager.
 */
App.Map = function(options, events) {

    // Private

    // The max extent must be the same as that set in tilecache.cfg. This
    // isn't the max extent of the map, but the TileCache layers' max
    // extent.
    var MAX_EXTENT = new OpenLayers.Bounds(420000, 30000, 900000, 350000);
    var WMTS_OPTIONS = {
        url: App.tilecacheURL,
        style: 'default',
        dimensions: ['TIME'],
        params: {
            'time': '2011'
        },
        matrixSet: 'swissgrild',
        maxExtent: MAX_EXTENT,
        isBaseLayer: true,
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

    /**
     * Method: createOrthoLayer
     * Returns the ortho layer.
     *
     * Returns:
     * {OpenLayers.Layer} a OpenLayers.Layer objects.
     */
    var createOrthoLayer = function() {
        return new OpenLayers.Layer.WMTS(Ext.applyIf({
            name: OpenLayers.i18n('ortho'),
            ref: 'ortho',
            layer: 'ortho',
            formatSuffix: 'jpeg',
            opacity: 0,
            isBaseLayer: false
        }, WMTS_OPTIONS));
    };


    /**
     * Method: createBaseLayers
     * Returns the list of layers.
     *
     * Returns:
     * {Array({OpenLayers.Layer})} An array of OpenLayers.Layer objects.
     */
    var createBaseLayers = function() {
        var layers = [];
        layers.push(new OpenLayers.Layer.WMTS(Ext.applyIf({
            name: OpenLayers.i18n('plan'),
            ref: 'plan',
            layer: 'plan'
        }, WMTS_OPTIONS)));
        layers.push(new OpenLayers.Layer.WMTS(Ext.applyIf({
            name: OpenLayers.i18n('plan color'),
            ref: 'plan_color',
            layer: 'plan_color'
        }, WMTS_OPTIONS)));
        layers.push(new OpenLayers.Layer(
            OpenLayers.i18n('blank'),
            {
                isBaseLayer: true, 
                displayInLayerSwitcher: false, 
                ref: 'blank'
            }));
        var defaultBaseLayer = App.functionality["default_basemap"] || "plan";
        var first = [];
        Ext.each(layers, function(layer, index){
            if (layer.ref == defaultBaseLayer) {
                first.push(layer);
                layers.remove(index);
                return false;
            }
        });
        return first.concat(layers);
    };

    /**
     * Method: createApiOverlays
     * Return WMS overlays for the map.
     *
     * Returns:
     * {OpenLayers.Layer.WMS} overlay layer instance.
     */
    var createApiOverlays = function(overlays, type) {
        var layers = [], themes = App["themes"][type];
        uppermost: for (var i = 0, len = overlays.length; i < len; i++) {
            var name = overlays[i];
            for (var j = 0, lenj = themes.length; j < lenj; j++) {
                var theme = themes[j];
                if (theme.name == name) {
                    layers = layers.concat(_getNodeChildren(theme));
                    continue uppermost;
                }
            }
            layers.push(name);
        }
        var params = {
            layers: layers,
            format: 'image/png'
        };
        if (type == 'external') {
            params.external = true;
        }
        return new OpenLayers.Layer.WMS("overlays_" + type, 
            App.mapserverproxyURL, params, {
            isBaseLayer: false,
            singleTile: true,
            ratio: 1,
            visibility: true
        });
    };

    /**
     * Method: _getNodeChildren
     * Gets the Mapserver layers associated to given theme node 
     *
     * Returns:
     * Array
     */
    var _getNodeChildren = function(node) {
        var children = [];
        if (node.children) {
            for (var i = 0, len = node.children.length; i < len; i++) {
                children = children.concat(_getNodeChildren(node.children[i]));
            }
        } else {
            children.push(node.name);
        }
        return children;
    };

    /**
     * Method: createOverviewMap
     * Create the overview map control.
     *
     * Returns:
     * {OpenLayers.Control.OverviewMap} The overview map.
     */
    var createOverviewMap = function(maxExtent) {
        var overviewMapLayer, extent, proj = null;
        if (App.overwiewImageType == 'osm') {
            var u = '.tile.openstreetmap.org/${z}/${x}/${y}.png';
            overviewMapLayer = new OpenLayers.Layer.OSM("OSM", [
                    'http://a'+u, 'http://b'+u, 'http://c'+u
                ], {
                    transitionEffect: 'resize',
                    buffer: 0,
                    attribution: [
                        "(c) <a href='http://openstreetmap.org/'>OSM</a>",
                        "<a href='http://creativecommons.org/licenses/by-sa/2.0/'>by-sa</a>"
                    ].join(' ')
                }
            );
            proj = new OpenLayers.Projection('EPSG:900913');
            var fromproj = new OpenLayers.Projection("EPSG:21781");
            extent = maxExtent.clone().transform(fromproj,proj);
        } else {
            overviewMapLayer = new OpenLayers.Layer.Image(
                OpenLayers.Util.createUniqueID("c2cgeoportal"),
                App.overwiewImage,
                OpenLayers.Bounds.fromArray(App.overwiewImageBounds),
                new OpenLayers.Size(
                    App.overwiewImageSize[0],
                    App.overwiewImageSize[1]),
                {isBaseLayer: true}
            );
            proj = new OpenLayers.Projection('EPSG:21781');
            extent = maxExtent;
        }


        return new OpenLayers.Control.OverviewMap({
            size: new OpenLayers.Size(200, 100),
            minRatio: 64, 
            maxRatio: 64, 
            layers: [overviewMapLayer],
            mapOptions: {
                theme: null, // for OpenLayers not to attempt to load the
                             // default theme
                projection: proj,
                units: 'm',
                maxExtent: extent,
                restrictedExtent: extent,
                numZoomLevels: 1
            }
        });
    };

    // Public

    Ext.apply(this, {

        /**
         * APIProperty: mapPanel
         * The {GeoExt.MapPanel} instance. Read-only.
         */
        mapPanel: null,

        /**
         * APIProperty: vectorLayer
         * The {OpenLayers.Layer.Vector} instance.
         */
        vectorLayer: null,

        /**
         * APIProperty: layerStore
         * The {GeoExt.data.LayerStore} instance.
         */
        layerStore: null
    });

    // Main

    // create map
    var maxExtent = OpenLayers.Bounds.fromArray(App.restrictedExtent);
    var mapOptions = {
        projection: new OpenLayers.Projection("EPSG:21781"),
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
            createOverviewMap(maxExtent)
        ]
    };
    var map = new OpenLayers.Map(mapOptions);

    // create layers, and add them to the map
    var baseLayers = createBaseLayers();
    var ortho      = createOrthoLayer();
    var layers     = Array.prototype.concat.call(
                        baseLayers, [ortho]);
    if (options.isApi && options.overlays) {
        var hasLocal = options.overlays.local;
        var hasExternal = options.overlays.external;
        if (hasLocal) {
            layers.push(createApiOverlays(options.overlays.local, 'local'));
        }
        if (hasExternal) {
            layers.push(createApiOverlays(options.overlays.external, 'external'));
        }
        if (!hasLocal && !hasExternal) {
            // if local/external is not specified, take overlays as local
            layers.push(createApiOverlays(options.overlays, 'local'));
        }
    }
    map.addLayers(layers);

    var layerStore = new GeoExt.data.LayerStore({layers: layers});
    map.events.on({
        'changelayer': function() {
            layerStore.map = this;
            layerStore.onChangeLayer.apply(layerStore, arguments);
            delete layerStore.map;
        }
    });

    // create tools for the toolbar
    var tools = new App.Tools(
        map, layerStore, ortho, events, options.isApi
    );
    this.legendPanel = tools.legendPanel;

    // create the map panel
    // we overload getState and applyState so "easting" and "northing"
    // are used in place of "x" and "y" in the permalink
    options = Ext.apply({
        map: map,
        tbar: tools.tbar,
        stateId: "map",
        prettyStateKeys: true,
        getState: function() {
            var state = GeoExt.MapPanel.prototype.getState.call(this);
            if (state) {
                state.easting = state.x;
                delete state.x;
                state.northing = state.y;
                delete state.y;
            }
            return state;
        },
        applyState: function(state) {
            state.x = state.easting;
            delete state.easting;
            state.y = state.northing;
            delete state.northing;
            GeoExt.MapPanel.prototype.applyState.apply(this, [state]);
        },
        // hack so that the map is not resized when querier pops up:
        updateMapSize: function(){}
    }, options);

    if (App['extent']) {
        Ext.apply(options, {
            extent: OpenLayers.Bounds.fromArray(App['extent'])
        });
    }
    var mapPanel = new GeoExt.MapPanel(options);

    addOpacitySlider = function() {
        var container = Ext.DomHelper.append(mapPanel.bwrap, {
            tag: 'div',
            cls: 'baseLayersOpacitySlider'
        }, true /* returnElement */);
        tools.mapbar.render(container);
        tools.mapbar.doLayout();
        var totalWidth = 0;
        tools.mapbar.items.each(function(item) {
            totalWidth += item.getWidth() + 5;
        });
        container.setWidth(totalWidth);
        container.setStyle({'marginLeft': (-totalWidth / 2) + 'px'});
    };
    if (options.isApi) {
        addOpacitySlider();
    }
    else {
        mapPanel.on({
            'render': addOpacitySlider,
            delay: 2000
        });
    }

    // make public properties visible
    this.mapPanel = mapPanel;
    this.layerStore = layerStore;
};

