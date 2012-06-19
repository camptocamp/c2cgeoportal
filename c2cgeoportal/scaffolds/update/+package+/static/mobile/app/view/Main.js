Ext.define("App.view.Main", {
    extend: 'Ext.Container',
    xtype: 'mainview',
    requires: [
        'Ext.field.Search',
        'Ext.field.Select',
        'App.model.Layer',
        'Ext.util.Geolocation'
    ],

    config: {
        map: null,
        layout: 'fit',
        items: [{
            xtype: 'toolbar',
            docked: 'top',
            items: [{
                xtype: 'searchfield',
                flex: 4,
                locales: {
                    placeHolder: 'views.map.search'
                },
                action: 'search'
            }, {
                xtype: 'spacer'
            }, {
                xtype: 'button',
                iconCls: 'layers',
                action: 'layers',
                iconMask: true
            }, {
                xtype: 'button',
                iconCls: 'settings',
                action: 'settings',
                iconMask: true
            }]
        }, {
            id: 'map-container'
        }, {
            xtype: 'button',
            cls: 'zoomin',
            iconCls: 'add',
            action: 'zoomin',
            iconMask: true,
            top: 51,
            left: 10
        }, {
            xtype: 'button',
            cls: 'zoomout',
            iconCls: 'minus1',
            action: 'zoomout',
            iconMask: true,
            top: 85,
            left: 10
        }, {
            xtype: 'button',
            iconCls: 'locate',
            action: 'locate',
            iconMask: true,
            top: 10,
            left: 10
        }, {
            xtype: 'selectfield',
            id: 'baselayer_switcher',
            width: 170,
            top: 10,
            right: 10,
            displayField: 'name',
            valueField: 'id'
        }]
    },

    initialize: function() {
        this.callParent(arguments);

        this.on('painted', this.render, this, {
            single: true
        });

        // base layer manager
        var baseLayerSwitcher = this.down('#baselayer_switcher');
        baseLayerSwitcher.on({
            'change': function(select, newValue) {
                // when applyMap adds layers to the base layer
                // store "change" is fired by the field, and
                // we don't have a map at that time yet
                var map = this.getMap();
                if (map) {
                    map.setBaseLayer(map.getLayer(newValue));
                }
            },
            scope: this
        });

        // zoom buttons
        this.down('[action=zoomin]').on({
            'tap': function() {
                this.getMap().zoomIn();
            },
            scope: this
        });
        this.down('[action=zoomout]').on({
            'tap': function() {
                this.getMap().zoomOut();
            },
            scope: this
        });

        var geolocation = Ext.create('Ext.util.Geolocation', {
            autoUpdate: false
        });
        this.down('[action=locate]').on({
            'tap': function() {
                geolocation.on('locationupdate', function(geo) {
                    var lonlat = new OpenLayers.LonLat(geo.getLongitude(),
                                                       geo.getLatitude());
                    lonlat.transform('EPSG:4326', map.getProjection());
                    this.getMap().setCenter(lonlat, 10);
                }, this, {single: true});
                geolocation.updateLocation();
            }
        });
    },

    applyMap: function(map) {
        var baseLayersStore = Ext.create('Ext.data.Store', {
            model: 'App.model.Layer'
        });
        Ext.each(map.layers, function(layer) {
            if (layer.isBaseLayer) {
                baseLayersStore.add(layer);
            }
        });
        this.down('#baselayer_switcher').setStore(baseLayersStore);
        return map;
    },

    destroy: function() {
        var map = this.getMap();
        if (map) {
            map.destroy();
        }
        this.callParent();
    },

    // initial rendering
    render: function(component) {
        var map = this.getMap();
        map.render(this.down('#map-container').element.dom);
        map.zoomToMaxExtent();
    },

    /**
     * Method: recenterOnFeature
     */
    recenterOnFeature: function(f) {
        if (f) {
            var lonlat = new OpenLayers.LonLat(f.lng, f.lat);
            lonlat.transform('EPSG:4326', this.getMap().getProjection());
            this.getMap().setCenter(lonlat, 13);
        }
    }
});
