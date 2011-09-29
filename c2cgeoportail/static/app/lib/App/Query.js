/*
 * @include OpenLayers/Control/WMSGetFeatureInfo.js
 * @include OpenLayers/Format/WMSGetFeatureInfo.js
 * @include OpenLayers/Format/GML.js
 * @include OpenLayers/Format/GML.js
 * @include OpenLayers/Request/XMLHttpRequest.js
 * @include GeoExt/widgets/Action.js
 */

Ext.namespace('App');

/**
 * Class: App.Query
 * Map queries (with WMS GetFeatureInfo)
 *
 * Options:
 * events - {Ext.util.Observable}The application events manager.
 * map - {OpenLayers.Map} The map.
 * tbar - {Ext.Toolbar} The toolbar.
 */
App.Query = function(options) {

    // Private

    options.events && options.events.addEvents('querystarts', 'queryresults');

    /**
     * Method: createAction
     * Create the GeoExt action.
     *
     * Returns:
     * {GeoExt.Action}
     */
    var createAction = function() {
        return new GeoExt.Action(Ext.applyIf({
            allowDepress: true,
            enableToggle: true,
            iconCls: 'info',
            tooltip: OpenLayers.i18n("Query.actiontooltip"),
            control: createControl()
        }, options));
    };

    /**
     * Method: createControl
     * Create the WMS GFI control.
     *
     * Returns:
     * {OpenLayers.Control.WMSGetFeatureInfo}
     */
    var createControl = function() {
        // we overload findLayers to avoid sending requests
        // when we have no sub-layers selected
        return new OpenLayers.Control.WMSGetFeatureInfo({
            infoFormat: "application/vnd.ogc.gml",
            maxFeatures: App.MAX_FEATURES || 100,
            queryVisible: true,
            drillDown: true,
            findLayers: function() {
                var wmsLayers = options.map.getLayersByClass("OpenLayers.Layer.WMS")
                for (var i = 0, len = wmsLayers.length ; i < len ; i++) {
                    var layer = wmsLayers[i];
                    if (layer.getVisibility() === true) {
                        var GFI = OpenLayers.Control.WMSGetFeatureInfo;
                        return GFI.prototype.findLayers.apply(this, arguments);
                    }
                }
                Ext.MessageBox.alert("Info",
                        OpenLayers.i18n("Query.nolayerselectedmsg"));
                return [];
            },

            // copied from OpenLayers.Control.WMSGetFeatureInfo and updated as
            // stated in comments
            request: function(clickPosition, options) {
                var layers = this.findLayers();
                if (layers.length == 0) {
                    this.events.triggerEvent("nogetfeatureinfo");
                    // Reset the cursor.
                    OpenLayers.Element.removeClass(this.map.viewPortDiv, "olCursorWait");
                    return;
                }

                options = options || {};
                if (this.drillDown === false) {
                    var wmsOptions = this.buildWMSOptions(this.url, layers,
                        clickPosition, layers[0].params.FORMAT);
                    var request = OpenLayers.Request.GET(wmsOptions);

                    if (options.hover === true) {
                        this.hoverRequest = request;
                    }
                } else {
                    // Following is specific code, updated from original
                    // OpenLayers.Control.WMSGetFeatureInfo code to make
                    // exactly one request by layer, so our mapserver proxy
                    // don't get lost.
                    this._requestCount = 0;
                    this._numRequests = layers.length;
                    this.features = [];
                    for (var i=0, len=layers.length; i<len; i++) {
                        var layer = layers[i];
                        var url = layer.url instanceof Array ? layer.url[0] : layer.url;
                        var wmsOptions = this.buildWMSOptions(url, [layer],
                            clickPosition, layer.params.FORMAT);
                        OpenLayers.Request.GET(wmsOptions);
                    }
                }
            },

            eventListeners: {
                beforegetfeatureinfo: function() {
                    options.events.fireEvent('querystarts');
                },
                getfeatureinfo: function(e) {
                    options.events.fireEvent('queryresults', e.features);
                },
                activate: function() {
                    options.events.fireEvent('queryopen');
                },
                deactivate: function() {
                    options.events.fireEvent('queryclose');
                }
            }
        });
    };

    // Main

    /**
     * APIProperty: action
     * {GeoExt.Action} GeoExt action configured with an
     *     OpenLayers WGI control.
     */
    this.action = createAction();
};
