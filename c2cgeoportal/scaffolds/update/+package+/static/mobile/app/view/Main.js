Ext.define("App.view.Main", {
    extend: 'Ext.Container',
    xtype: 'mainview',
    requires: [
        'Ext.field.Search',
        'Ext.field.Select',
        'Ext.SegmentedButton',
        'App.model.Layer',
        'App.plugin.StatefulMap'
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
            new Geolocate()
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

var Geolocate = OpenLayers.Class(OpenLayers.Control, {

    autoActivate: true,
    button: null,
    firstGeolocation: false,

    activate: function() {
        if(!OpenLayers.Control.prototype.activate.apply(this, arguments)) {
            return false;
        }
        var options = {
            displayInLayerSwitcher: false,
            calculateInRange: OpenLayers.Function.True
        };
        this.layer = new OpenLayers.Layer.Vector(this.CLASS_NAME, options);
        this.touchControl = this.map.getControlsByClass('OpenLayers.Control.TouchNavigation')[0];

        this.circle = new OpenLayers.Feature.Vector(
            null,
            {},
            {
                fillOpacity: 0.1,
                strokeOpacity: 0.6
            }
        );
        this.marker = new OpenLayers.Feature.Vector(
            null,
            {},
            OpenLayers.Util.applyDefaults({
                graphicOpacity: 1,
                graphicWidth: 16,
                graphicHeight: 16
            }, OpenLayers.Feature.Vector.style['default'])
        );

        return true;
    },

    draw: function() {
        var div = OpenLayers.Control.prototype.draw.apply(this);

        var geolocate = document.createElement("a");
        div.appendChild(geolocate);
        OpenLayers.Element.addClass(geolocate, "olButton");
        this.button = geolocate;

        this.eventsInstance = this.map.events;
        this.eventsInstance.register("buttonclick", this, this.onClick);

        this.geolocateControl = new OpenLayers.Control.Geolocate({
            bind: false,
            autoCenter: false,
            watch: true,
            geolocationOptions: {
                enableHighAccuracy: true,
                maximumAge: 0,
                timeout: 7000
            }
        });
        this.geolocateControl.events.register("locationfailed", this, function(e) {
            if (e.error.code == 1) {
                this.geolocateControl.deactivate();
                this.cancelAutoUpdate();
                alert("This application is not allowed to use your position");
            }
        });
        this.geolocateControl.events.register("locationupdated", this, function(e) {
            this.layer.removeFeatures([this.circle, this.marker]);
            this.circle.geometry = new OpenLayers.Geometry.Polygon.createRegularPolygon(
                e.point,
                e.position.coords.accuracy/2,
                40,
                0
            );
            this.marker.geometry = e.point;
            this.layer.addFeatures([
                this.circle,
                this.marker
            ]);
            this.map.events.unregister('movestart', this, this.cancelAutoUpdate);
            if (this.firstGeolocation) {
                this.map.addLayer(this.layer);
                this.map.zoomToExtent(this.circle.geometry.getBounds());
                this.firstGeolocation = false;
            } else if (this.geolocateControl.autoCenter) {
                this.map.setCenter(new OpenLayers.LonLat(e.point.x, e.point.y));
            }
            this.map.events.register('movestart', this, this.cancelAutoUpdate);
        });

        return div;
    },

    // cancel auto update if map is drag-panned
    cancelAutoUpdate: function(evt) {
        if (!evt || !evt.zoomChanged) {
            // control is still active, but map doesn't recenter
            this.geolocateControl.autoCenter = false;
            this.touchControl.pinchZoom.preserveCenter = false;
            OpenLayers.Element.removeClass(this.button, 'active');
            this.firstGeolocation = false;
            this.circle.style.fillColor = '#999';
            this.circle.style.strokeColor = '#999';
            this.marker.style.externalGraphic = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAQAAAC1+jfqAAAAAXNSR0IArs4c6QAAAAJiS0dEAP+Hj8y/AAAACXBIWXMAAAsTAAALEwEAmpwYAAAAB3RJTUUH3AwDDSwgdOrsLgAAARhJREFUKM+FkT1uwkAQhb+1LIi9hkhJYxHlApYotuAWHIAyDXS5AgVXSIeblBzAd6CgcOeKigjFBUkRfgTsbqBYisSRyDxpNMXTSN974sT18eHFXQk9uiggJ2NCAfCMD990mPX90X18RwRs1Kf66JthJ525D4ZpPxw/cgtYIOCBKH4bTyEFD2wiRi0k5ockLcTIJuCB7jXjAF1RQDPWPfDAdBsc/hgONDBd8EGrd7aENAipAwd2rNkh0coZsHyxqvDXuEE7Cp1L1WRTMURIdO4ws5WKEJhf+YWsMJmjmJSlRSIJLpJILGWpJy6H4jhcsKdGndpl71lwHNrCYdJO14N5uWSLh8eWJfNyPWinBhAnnq6U9Yr4r+4zk2Z4mbISFUIAAAAASUVORK5CYII%3D';
            this.layer.redraw();
        }
    },

    onClick: function(evt) {
        var button = evt.buttonElement;
        if (button === this.button) {
            if (this.button.className.indexOf('active') != -1) {
                this.cancelAutoUpdate();
            } else {
                this.map.addControl(this.geolocateControl);
                this.geolocateControl.autoCenter = true;
                this.firstGeolocation = true;
                // force activation, even if already active
                this.geolocateControl.deactivate();
                this.geolocateControl.activate();
                OpenLayers.Element.addClass(this.button, 'active');
                this.touchControl.pinchZoom.preserveCenter = true;
                this.circle.style.fillColor = '#4C7FB2';
                this.circle.style.strokeColor = '#4C7FB2';
                this.marker.style.externalGraphic = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABGdBTUEAAK/INwWK6QAAABl0RVh0U29mdHdhcmUAQWRvYmUgSW1hZ2VSZWFkeXHJZTwAAAGYSURBVHjapFNLisJAEK2E4Cf+QDeieAHBRZjxFh7ACyTewoW3MF7AA3iHLDKDO1euFNFF4sIfGn9Tr0alF+LA2PDSTdWrl9Srjna9XumdpUGg5X6rsSqjyWgwrFtsyBgw+ozRndh1PsjA4XK5UL1eJ9/3bcMwOoVCoZjP5ymdTgtxs9lYy+XSCsPQPp1Obeb2mCs5EeAgeZ5nm6bpVioVyuVykjyfz7Ink0kql8sQLE6nU5e5CPfw0G/EqqZpnVKpRKlUSgSfATlwwEXNQ+B4PDaz2WwRb+LzS4ADLmoeAqzeyGQydDgc/hQAB1zUPDzghDWfz2m73RL7IATs8XhcPEDRbrej9XotO1pBjSoghq1WKwqC4OXcY7EYJRIJqVEFhqxqcW8Y2UsBjPb2BUN1jAN+s4UkOyyOP1t8R6Q1fCVq1Cn0F7zQBtQBuK3iHgcHXNSo92AURVF7MpnQfr+XPmEgdvWMHDjgokYdI9VqtR677IzH48VsNpOJ6LouwBkx5MAB996m/EyfLfdfP9NX1/kVeGf9CDAAGzQxvrg3al4AAAAASUVORK5CYII%3D';
                this.layer.redraw();
            }
        }
    },

    /**
* Method: destroy
* Clean up.
*/
    destroy: function() {
        if (this.map) {
            this.map.events.unregister("buttonclick", this, this.onClick);
        }
        OpenLayers.Control.prototype.destroy.apply(this);
    },

    CLASS_NAME: "Geolocate"
});
