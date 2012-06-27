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
        var mapContainer = this.down('#map-container').element;
        map.render(mapContainer.dom);
        map.zoomToMaxExtent();

        mapContainer.on('longpress', function(event, node) {
            // FIXME: depends on https://github.com/openlayers/openlayers/pull/294
            var map = this.getMap();
            var el = Ext.get(map.div);
            var pixel = new OpenLayers.Pixel(
                event.pageX - el.getX(),
                event.pageY - el.getY()
            );
            var bounds = this.pixelToBounds(pixel);
            this.fireEvent('longpress', this, bounds, map, event);
        }, this);
    },
    
    /**
     * Method: pixelToBounds
     * Takes a pixel as argument and creates bounds after adding the
     * <clickTolerance>.
     * 
     * Parameters:
     * pixel - {<OpenLayers.Pixel>}
     */
    pixelToBounds: function(pixel) {
        var tolerance = 40;
        var llPx = pixel.add(-tolerance/2, tolerance/2);
        var urPx = pixel.add(tolerance/2, -tolerance/2);
        var ll = this.getMap().getLonLatFromPixel(llPx);
        var ur = this.getMap().getLonLatFromPixel(urPx);
        return new OpenLayers.Bounds(
            parseInt(ll.lon),
            parseInt(ll.lat),
            parseInt(ur.lon),
            parseInt(ur.lat)
        );
    },

    /**
     * Method: recenterOnFeature
     */
    recenterOnFeature: function(f) {
        if (f) {
            var bbox = new OpenLayers.Bounds.fromArray(f.bbox);
            this.getMap().zoomToExtent(bbox);
        }
    }
});
