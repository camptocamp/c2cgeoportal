Ext.define("App.view.Main", {
    extend: 'Ext.Container',
    xtype: 'mainview',
    requires: [
        'Ext.field.Search',
        'Ext.field.Select',
        'Ext.SegmentedButton',
        'App.model.Layer',
        'App.plugin.StatefulMap',
        'App.view.GeolocateControl'
    ],

    config: {
        map: null,
        layout: 'fit',
        plugins: 'statefulmap',
        vectorLayer: null,
        center: null,
        zoom: null,
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
            xtype: 'selectfield',
            id: 'baselayer_switcher',
            width: 170,
            top: 10,
            right: 10,
            displayField: 'name',
            valueField: 'id',
            defaultPhonePickerConfig: {
                cancelButton: OpenLayers.i18n('layer_switcher.cancel'),
                doneButton: OpenLayers.i18n('layer_switcher.done')
            }
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

    updateMap: function(map) {
        this.fireEvent('setmap', this, map);
    },


    destroy: function() {
        var map = this.getMap();
        if (map) {
            map.destroy();
        }
        this.callParent();
    },

    setCenterZoomFromQueryParams: function() {
        var queryParams = OpenLayers.Util.getParameters();
        if (queryParams.x && queryParams.y && queryParams.zoom) {
            this.setCenter(
                new OpenLayers.LonLat(queryParams.x, queryParams.y));
            this.setZoom(queryParams.zoom);
        }
    },

    // initial rendering
    render: function(component) {
        var map = this.getMap();
        var mapContainer = this.down('#map-container').element;
        map.render(mapContainer.dom);

        this.setCenterZoomFromQueryParams();

        var center = this.getCenter(),
            zoom = this.getZoom();
        if (center && zoom) {
            map.setCenter(center, zoom);
        } else {
            map.zoomToMaxExtent();
        }

        mapContainer.on('longpress', function(event, node) {
            var map = this.getMap();
            var el = Ext.get(map.div);
            var pixel = new OpenLayers.Pixel(
                event.pageX - el.getX(),
                event.pageY - el.getY()
            );
            var bounds = this.pixelToBounds(pixel);
            this.fireEvent('longpress', this, bounds, map, event);
        }, this);

        // highlight layer
        this.setVectorLayer(new OpenLayers.Layer.Vector('Vector', {
            styleMap: new OpenLayers.StyleMap(OpenLayers.Util.applyDefaults({
                strokeWidth: 3,
                strokeColor: 'red'
            }, OpenLayers.Feature.Vector.style['default']))
        }));
        map.addLayer(this.getVectorLayer());

        map.addControls([
            new OpenLayers.Control.Zoom(),
            new App.view.GeolocateControl()
        ]);
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
            var layer = this.getVectorLayer();
            layer.destroyFeatures();
            layer.addFeatures(f);

            var map = this.getMap();
            if (f.geometry instanceof OpenLayers.Geometry.Point) {
                map.setCenter(
                    [f.geometry.x, f.geometry.y],
                    map.baseLayer.numZoomLevels - 3
                );
            } else {
                map.zoomToExtent(f.geometry.getBounds());
            }
            map.events.register('moveend', this, function onmoveend() {
                layer.removeFeatures(f);
                // call the event only once
                map.events.unregister('moveend', this, onmoveend);
            });
        }
    }
});
