Ext.define("App.view.Main", {
    extend: 'Ext.Container',
    xtype: 'mainview',
    requires: [
        'Ext.field.Search',
        'Ext.field.Select',
        'Ext.SegmentedButton',
        'App.model.Layer',
        'App.plugin.StatefulMap',
        'Ext.util.Geolocation'
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
            xtype: 'segmentedbutton',
            allowMultiple: false,
            top: 10,
            left: 10,
            items: [{
                iconCls: 'locate',
                cls: 'locate',
                action: 'locate',
                pressed: false,
                iconMask: true
            }]
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

        var geolocateControl = new OpenLayers.Control.Geolocate({
            bind: false,
            autoCenter: false,
            watch: true,
            geolocationOptions: {
                enableHighAccuracy: true,
                maximumAge: 0,
                timeout: 7000
            }
        });
        var firstGeolocation,
            circle,
            marker;
        geolocateControl.events.register("locationupdated", this, function(e) {
            if (circle && marker) {
                this.getVectorLayer().removeFeatures([circle, marker]);
            }
            circle = new OpenLayers.Feature.Vector(
                OpenLayers.Geometry.Polygon.createRegularPolygon(
                    e.point,
                    e.position.coords.accuracy/2,
                    40,
                    0
                ),
                {},
                {
                    fillOpacity: 0.1,
                    fillColor: '#4C7FB2',
                    strokeColor: '#4C7FB2',
                    strokeOpacity: 0.6
                }
            );
            marker = new OpenLayers.Feature.Vector(
                e.point,
                {},
                OpenLayers.Util.applyDefaults({
                    externalGraphic: 'resources/images/locate_marker.png',
                    graphicOpacity: 1,
                    graphicWidth: 16,
                    graphicHeight: 16
                }, OpenLayers.Feature.Vector.style['default'])
            );
            this.getVectorLayer().addFeatures([
                circle,
                marker
            ]);
            var map = this.getMap();
            map.events.un({'moveend': cancelAutoUpdate});
            if (firstGeolocation) {
                map.zoomToExtent(circle.geometry.getBounds());
                firstGeolocation = false;
            } else if (geolocateControl.autoCenter) {
                map.setCenter(new OpenLayers.LonLat(e.point.x, e.point.y));
            }
            map.events.on({'moveend': cancelAutoUpdate});
        });

        var locateButton = this.down('[action=locate]');
        function cancelAutoUpdate() {
            // control is still active, but map doesn't recenter
            geolocateControl.autoCenter = false;
            locateButton.parent.setPressedButtons([]);
            firstGeolocation = false;
        }
        locateButton.on({
            'tap': function(button) {
                var map = this.getMap();
                map.addControl(geolocateControl);

                var parent = button.parent;
                if (parent.getPressedButtons().indexOf(button) != -1) {
                    button.parent.setPressedButtons([button]);
                    geolocateControl.autoCenter = true;
                    firstGeolocation = true;
                    // force activation, even if already active
                    geolocateControl.deactivate();
                    geolocateControl.activate();
                } else {
                    cancelAutoUpdate();
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

    // initial rendering
    render: function(component) {
        var map = this.getMap();
        var mapContainer = this.down('#map-container').element;
        map.render(mapContainer.dom);

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

        // highlight and geolocate layer
        this.setVectorLayer(new OpenLayers.Layer.Vector('Vector', {
            styleMap: new OpenLayers.StyleMap(OpenLayers.Util.applyDefaults({
                strokeWidth: 3,
                strokeColor: 'red'
            }, OpenLayers.Feature.Vector.style['default']))
        }));
        map.addLayer(this.getVectorLayer());
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
