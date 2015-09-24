/**
 * Copyright (c) 2011-2014 by Camptocamp SA
 *
 * CGXP is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * CGXP is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with CGXP. If not, see <http://www.gnu.org/licenses/>.
 */

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
                xtype: 'mysearchfieldnestedinaform',
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
                action: 'layers'
            }, {
                xtype: 'button',
                iconCls: 'settings',
                action: 'settings'
            }]
        }, {
            xtype: 'component',
            id: 'map-container',
            height: '100%',
            style: {
                position: 'relative',
                zIndex: 0
            }
        }]
    },

    initialize: function() {
        this.callParent(arguments);

        this.on('painted', this.render, this, {
            single: true
        });
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

    setOverlaysVisibility: function() {
        var map = this.getMap(),
            layers = map.layers,
            numLayers = layers.length,
            layer,
            i;
        for (i=0; i<numLayers; ++i) {
            layer = layers[i];
            if (layer.params && layer.params.hasOwnProperty('LAYERS') &&
                layer.params.LAYERS.length === 0) {
                layer.setVisibility(false);
            }
        }
    },

    // initial rendering
    render: function(component) {
        var map = this.getMap();
        var mapContainer = this.down('#map-container').element;

        map.render(mapContainer.dom);

        this.setOverlaysVisibility();
        this.setCenterZoomFromQueryParams();

        var center = this.getCenter(),
            zoom = this.getZoom();
        if (center && zoom) {
            map.setCenter(center, zoom);
        } else if (!map.getCenter()) {
            map.zoomToMaxExtent();
        }

        // highlight layer
        this.setVectorLayer(new OpenLayers.Layer.Vector('Vector', {
            styleMap: new OpenLayers.StyleMap(OpenLayers.Util.applyDefaults({
                strokeWidth: 3,
                strokeColor: 'red'
            }, OpenLayers.Feature.Vector.style['default']))
        }));
        map.addLayer(this.getVectorLayer());

        this.addQueryControls(mapContainer);

        map.addControls([
            new OpenLayers.Control.Zoom(),
            new App.GeolocateControl(),
            new App.MobileMeasure()
        ]);
    },

    /**
     * Method: addQueryControls
     * Adds a longpress or a single click event listener for queries.
     *
     * Parameters:
     * mapContainer - {<DOMElement>}
     */
    addQueryControls: function(mapContainer) {
        if (["click", "both"].indexOf(App.queryMode) !== -1) {
            var self = this;
            OpenLayers.Control.Click = OpenLayers.Class(OpenLayers.Control, {
                autoActivate: true,
                initialize: function(options) {
                    OpenLayers.Control.prototype.initialize.apply(
                        this, arguments
                    );
                    this.handler = new OpenLayers.Handler.Click(
                        this,
                        {
                            'click': function(evt) {
                                self.handleQueryEvents(evt.xy);
                            }
                        },
                        {
                            pixelTolerance: 5,
                            'single': true
                        }
                    );
                }
            });

            this.getMap().addControl(new OpenLayers.Control.Click({}));
        }
        if (["longpress", "both"].indexOf(App.queryMode) !== -1) {
            mapContainer.on('longpress', function(event, node) {
                var map = this.getMap();
                var el = Ext.get(map.div);
                var pixel = new OpenLayers.Pixel(
                    event.pageX - el.getX(),
                    event.pageY - el.getY()
                );
                this.handleQueryEvents(pixel);
            }, this);
        }
    },

    /**
     * Method: handleQueryEvents
     * Takes a pixel as argument and sends a query event.
     *
     * Parameters:
     * pixel - {<OpenLayers.Pixel>}
     */
    handleQueryEvents: function(pixel) {
        var map = this.getMap();
        var bounds = this.pixelToBounds(pixel);
        this.fireEvent('query', this, bounds, map);
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
            parseInt(ll.lon, 10),
            parseInt(ll.lat, 10),
            parseInt(ur.lon, 10),
            parseInt(ur.lat, 10)
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
            } else if (f.geometry) {
                map.zoomToExtent(f.geometry.getBounds());
            } else if (f.bounds) {
                map.zoomToExtent(f.bounds);
            }
            map.events.register('moveend', this, function onmoveend() {
                layer.removeFeatures(f);
                // call the event only once
                map.events.unregister('moveend', this, onmoveend);
            });
        }
    }
});

// see http://www.sencha.com/forum/showthread.php?151529-searchfield-not-showing-quot-Search-quot-button-on-iOS-keyboard.-Bug&p=945810&viewfull=1#post945810
Ext.define('MySearchFieldNestedInAForm', {
    extend: 'Ext.field.Search',
    xtype: 'mysearchfieldnestedinaform',

    getElementConfig: function() {
        var tpl = this.callParent();

        tpl.tag = 'form';
        tpl.onsubmit = 'return false;';

        return tpl;
    }
});
