/*
 * @requires GeoExt/data/FeatureReader.js
 *
 * @include OpenLayers/Format/GeoJSON.js
 * @include GeoExt/data/FeatureStore.js
 * @include App/TwinTriggerComboBox.js
 */

Ext.namespace("App");

/**
 * Class: App.Search
 * The text search UI.
 *
 * Parameters:
 * map - {OpenLayers.Map} The map.
 */
App.Search = function(map) {

    // Private

    /**
     * Method: createStore
     *
     * Returns:
     * {GeoExt.data.FeatureStore} The feature store.
     */
    var createStore = function() {
        var store = new GeoExt.data.FeatureStore({
            proxy: new Ext.data.ScriptTagProxy({
                url: App["fullTextSearchURL"],
                callbackParam: 'callback'
            }),
            baseParams: {
                "limit": 20
            },
            reader: new App.Search.FeatureReader({
                format: new OpenLayers.Format.GeoJSON()
            }, ['label', 'layer_name'])
        });

        store.on('beforeload', function(store, options) {
            var coords = store.baseParams.query.match(
                /([\d\.']+)[\s,]+([\d\.']+)/
            );
            if (coords) {
                var left = parseFloat(coords[1].replace("'", ""));
                var right = parseFloat(coords[2].replace("'", ""));
                // for switzerland:
                // EPSG:21781: lon > lat
                // EPSG:4326 : lat > lon
                var position = new OpenLayers.LonLat(
                    left > right ? left : right,
                    right < left ? right : left);
                var valid = false;
                if (map.maxExtent.containsLonLat(position)) {
                    // try with EPSG:21781
                    valid = true;
                } else {
                    // try with EPSG:4326
                    position = new OpenLayers.LonLat(
                        left < right ? left : right,
                        right > left ? right : left);
                    position.transform(
                        new OpenLayers.Projection("EPSG:4326"),
                        map.getProjectionObject());
                    if (map.maxExtent.containsLonLat(position)) {
                        valid = true;
                    }
                }
                if (valid) {
                    map.setCenter(position, 8);
                }
            }
            return !coords;
        });

        return store;
    };

    /**
     * Method: createCombo
     *
     * Returns:
     * {Ext.form.ComboBox} The search combo.
     */
    var createCombo = function() {
        var tpl = new Ext.XTemplate(
            '<tpl for="."><div class="x-combo-list-item">',
            '{label}',
            '</div></tpl>'
        );
        var combo = new Ext.ux.form.TwinTriggerComboBox({
            store: createStore(),
            tpl: tpl,
            minChars: 1,
            queryDelay: 50,
            emptyText: OpenLayers.i18n('Search.emptytext'),
            loadingText: OpenLayers.i18n('Search.loadingtext'),
            displayField: 'label',
            triggerAction: 'all',
            trigger2Class: 'x-form-trigger-no-width x-hidden',
            trigger3Class: 'x-form-trigger-no-width x-hidden',
            width: 200,
            selectOnFocus: true
        });
        combo.on('select', function(combo, record, index) {
            // add feature to vector layer
            var feature = record.getFeature();
            vectorLayer.removeFeatures(vectorLayer.features);
            vectorLayer.addFeatures([feature]);
            // make sure the layer this feature belongs to is displayed
            var layer = map.getLayersBy('ref', record.get('layer_name'));
            if (layer && layer.length > 0) {
                layer[0].setVisibility(true);
            }
            // zoom onto the feature
            map.zoomToExtent(feature.bounds);
        });
        combo.on('clear', function(combo) {
            vectorLayer.removeFeatures(vectorLayer.features);
        });

        combo.on('render', function() {
            new Ext.ToolTip({
                target: combo.getEl(),
                title: OpenLayers.i18n('Search.Search'),
                width: 500,
                contentEl: 'search-tip',
                trackMouse:true,
                dismissDelay: 15000
            });
        });
        return combo;
    };

    // Main

    // a Search object has its own vector layer, which is added
    // to the map once for good
    var vectorLayer = new OpenLayers.Layer.Vector(
        OpenLayers.Util.createUniqueID("c2cgeoportal"),
        {displayInLayerSwitcher: false, alwaysInRange: true}
    );
    map.addLayer(vectorLayer);

    /**
     * APIProperty: combo
     * {Ext.form.ComboBox} The search combo.
     */
    this.combo = createCombo();
};

/**
 * Class: App.Search.FeatureReader
 * A FeatureReader that can be configured with a format.
 *
 * TODO: this code should be in GeoExt.
 */
App.Search.FeatureReader = Ext.extend(GeoExt.data.FeatureReader, {
    readRecords: function(features) {
        if (this.meta.format) {
            features = this.meta.format.read(features);
        }
        return GeoExt.data.FeatureReader.prototype.readRecords.call(
            this, features
        );
    }
});
