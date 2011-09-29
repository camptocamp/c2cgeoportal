/*
 * @include Styler/widgets/FilterBuilder.js
 * @include GeoExt/data/AttributeStore.js
 * @include OpenLayers/Protocol/WFS/v1_1_0.js
 * @include OpenLayers/Format/WFSDescribeFeatureType.js
 * @include OpenLayers/Feature/Vector.js
 * @include OpenLayers/Layer/Vector.js
 * @include OpenLayers/Util.js
 * @include OpenLayers/StyleMap.js
 * @include OpenLayers/Style.js
 */

Ext.namespace('App');

// Maximum number of features returned by query
App.MAX_FEATURES = App.MAX_FEATURES || 100;

App.QueryBuilder = function(events, options) {
    
    /**
     * Property: panel
     * {Ext.Panel} The panel included in accordion panel with a card layout
     */
    var panel;
    
    /**
     * Property: querierPanel
     * {Ext.Panel} The querier panel (child of panel)
     */
    var querierPanel;
    
    /**
     * Property: store
     * {GeoExt.data.AttributeStore} The store containing the properties of the Liegenshaften layer
     */
    var store;
    
    /**
     * Property: geometryName
     * {String} The name of the geom field
     */
    var geometryName;
    
    /**
     * Property: protocol
     * {OpenLayers.Protocol.WFS}
     */
    var protocol;
    
    /**
     * Property: featureType
     * {String} The name of the mapserver layer
     */
    var featureType = App["queryBuilderLayer"];
    
    /**
     * Property: drawingLayer
     * {OpenLayers.Layer.Vector}
     */
    var drawingLayer;
    
    /**
     * Property: mask
     * {Ext.LoadMask}
     */
    var mask;
    
    /**
     * Method: checkFilter
     * Checks that a filter is not missing items.
     *
     * Parameters:
     * filter - {OpenLayers.Filter} the filter
     *
     * Returns:
     * {Boolean} Filter is correct ?
     */
    var checkFilter = function(filter) {
        var filters = filter.filters || [filter];
        for (var i=0, l=filters.length; i<l; i++) {
            var f = filters[i];
            if (f.CLASS_NAME == 'OpenLayers.Filter.Logical') {
                if (!checkFilter(f)) {
                    return false;
                }
            } else if (!(f.value && f.type && 
                (f.property || f.CLASS_NAME == "OpenLayers.Filter.Spatial"))) {
                alert(OpenLayers.i18n("QueryBuilder.incomplete_form"));
                return false;
            } else if (f.CLASS_NAME == "OpenLayers.Filter.Comparison") {
                f.matchCase = false;
            }
        }
        return true;
    };
    
    /**
     * Method: search
     * Gets the Filter Encoding string and sends the getFeature request
     */
    var search = function() {
        var btn = this;
        
        // we quickly check if nothing lacks in filter
        var filter = panel.get(1).getFilter();
        if (!checkFilter(filter)) {
            return;
        }
        btn.setIconClass('loading');
        events.fireEvent("querystarts");
        
        // we deactivate draw controls before the request is done.
        panel.get(1).deactivateControls();
        
        protocol.read({
// don't work with actual version of mapserver, the proxy will limit to 200
// features to protect the browser.
//            maxFeatures: App.MAX_FEATURES || 100,
            filter: filter,
            callback: function(response) {
                btn.setIconClass(btn.initialConfig.iconCls);
                if (!response.success()) {
                    alert(OpenLayers.i18n('QueryBuilder.getfeature_exception'));
                    return;
                }
                if (response.features && response.features.length) {
                    var fs = response.features, l = fs.length;
                    // required by ResultsPanel:
                    while(l--) {
                        fs[l].type = featureType;
                    }
                    events.fireEvent("queryresults", fs);
                } else {
                    alert(OpenLayers.i18n('QueryBuilder.no_result'));
                }
            },
            scope: this
        });
    };
    
    var createQuerierPanel = function() {
        
        var style = OpenLayers.Util.extend({},
            OpenLayers.Feature.Vector.style['default']);

        var styleMap = new OpenLayers.StyleMap({
            "default": new OpenLayers.Style(
                OpenLayers.Util.extend(style, {
                    strokeWidth: 2,
                    strokeColor: "#ee5400",
                    fillOpacity: 0
                })
            )
        });
        
        drawingLayer = new OpenLayers.Layer.Vector('filter_builder', {
            displayInLayerSwitcher: false,
            styleMap: styleMap
        });
        
        querierPanel = panel.add({
            xtype: 'gx_filterbuilder',
            preComboText: OpenLayers.i18n("QueryBuilder.match"),
            postComboText: OpenLayers.i18n("QueryBuilder.of"),
            comboConfig: {
                width: 80
            },
            defaultBuilderType: Styler.FilterBuilder.ALL_OF,
            filterPanelOptions: {
                attributesComboConfig: {
                    displayField: "displayName",
                    listWidth: 200
                },
                values: {
                    storeUriProperty: 'url',
                    storeOptions: {
                        root: 'items',
                        fields: ['label', 'value']
                    },
                    comboOptions: {
                        displayField: 'label',
                        valueField: 'value'
                    }
                }
            },
            allowGroups: false,
            noConditionOnInit: false,
            deactivable: true,
            autoScroll: true,
            buttons: [{
                text: OpenLayers.i18n('QueryBuilder.query_btn_text'),
                iconCls: 'query',
                handler: search
            }],
            map: options.map, 
            attributes: store,
            allowSpatial: true,
            vectorLayer: drawingLayer
        });
        panel.layout.setActiveItem(1);
    };
    
    var createProtocol = function() {
        var idx = store.find('type', 
            /^gml:(Multi)?(Point|LineString|Polygon|Curve|Surface|Geometry)PropertyType$/);
        if (idx > -1) { 
            // we have a geometry
            var r = store.getAt(idx);
            geometryName = r.get('name');
            store.remove(r);
        } else {
            alert(OpenLayers.i18n("QueryBuilder.alert_no_geom_field"));
            return;
        }
        
        protocol = new OpenLayers.Protocol.WFS({
            url: App.mapserverproxyURL,
            featureType: featureType,
            featureNS: "http://mapserver.gis.umn.edu/mapserver",
            srsName: "EPSG:21781", // FIXME ?
            version: "1.1.0",
            geometryName: geometryName
        });
    };
    
    var onPanelExpanded = function() {
        if (drawingLayer) {
            drawingLayer.setVisibility(true);
        }
        if (querierPanel) {
            // child panel already created => exit
            return;
        }
        if (!mask) {
            window.setTimeout(function() {
                mask = new Ext.LoadMask(panel.body.dom, {
                    msg: OpenLayers.i18n('QueryBuilder.loading')
                });
                mask.show();
            }, 10);
        }
        if (!store) {
            store = new GeoExt.data.AttributeStore({
                url: App.mapserverproxyURL,
                fields: ["name", "type", "displayName"],
                baseParams: {
                    "TYPENAME": featureType,
                    "REQUEST": "DescribeFeatureType",
                    "SERVICE": "WFS",
                    "VERSION": "1.0.0"
                },
                listeners: {
                    "load": function() {
                        // one shot listener:
                        store.purgeListeners();
                        // attributes translation:
                        store.each(function(r) {
                            r.set("displayName", OpenLayers.i18n(r.get("name")));
                            if (App.filters && App.filters[r.get('name')]) {
                                r.set('type', r.get('type').replace(/xsd:/, ''));
                                r.set('url', App.filters[r.get('name')]);
                            }
                        });
                        createProtocol();                        
                        createQuerierPanel();
                        if (mask) {
                            mask.hide();
                        }
                    },
                    "loadexception": function() {
                        if (mask) {
                            mask.hide();
                        }
                        alert(OpenLayers.i18n("QueryBuilder.describefeaturetype_exception"));
                    }
                }
            });
        }
        store.load();
    };
    
    panel = new Ext.Panel(Ext.apply({
        layout: 'card',
        activeItem: 0,
        defaults: {
            border: false
        },
        items: [{
            html: " "
        }],
        listeners: {
            "expand": onPanelExpanded,
            "collapse": function() {
                if (drawingLayer) {
                    drawingLayer.setVisibility(false);
                }
                events.fireEvent("queryclose");
            }
        }
    }, options));

    this.panel = panel;
};

