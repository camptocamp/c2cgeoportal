/**
 * Copyright (c) 2011-2013 by Camptocamp SA
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

Ext.define('App.controller.Query', {
    extend: 'Ext.app.Controller',

    config: {
        protocol: null,
        refs: {
            queryView: {
                selector: 'queryview',
                xtype: 'queryview',
                autoCreate: true
            },
            queryViewList: {
                selector: 'queryview list'
            }
        },
        control: {
            queryViewList: {
                disclose: function(list, record) {
                    this.getApplication().getController('Main').recenterMap(record.raw);
                }
            }
        },
        routes: {
            'query/:coords': {
                action: 'showQueryResultView',
                condition: '.+'
            }
        }
    },

    //called when the Application is launched, remove if not needed
    launch: function(app) {
        this.protocol = new OpenLayers.Protocol.WFS({
            url: App.wmsUrl,
            geometryName: 'geom',
            srsName: App.map.getProjection(),
            formatOptions: {
                featureNS: 'http://mapserver.gis.umn.edu/mapserver',
                autoconfig: false
            }
        });
    },

    showQueryResultView: function(params) {
        var store = this.getQueryView().down('list').getStore();
        store.removeAll();

        params = decodeURIComponent(params);
        params = params.split('-');
        var bounds = params[0].split(',');

        bounds = new OpenLayers.Bounds.fromArray(bounds);
        var filter = new OpenLayers.Filter.Spatial({
            type: OpenLayers.Filter.Spatial.BBOX,
            value: bounds
        });
        this.protocol.format.featureType = params[1].split(',');
        var response = this.protocol.read({
            maxFeatures: 20,
            filter: filter,
            callback: function(result) {
                if(result.success()) {
                    if(result.features.length) {
                        store.add(result.features);
                    }
                }
            }
        });

        if (App.raster) {
            var coords = this.getQueryView().down('[pseudo=coordinates]');
            var x = (bounds.right - bounds.left) / 2 + bounds.left;
            var y = (bounds.top - bounds.bottom) / 2 + bounds.bottom;
            coords.setTpl(OpenLayers.i18n('rasterTpl'));
            Ext.Ajax.request({
                url: App.rasterUrl,
                method: 'GET',
                params: {
                    lon: x,
                    lat: y
                },
                success: function(response) {
                    var data = Ext.JSON.decode(response.responseText);
                    Ext.apply(data, {
                        x: x,
                        y: y
                    });
                    coords.setData(data);
                }
            });
        }

        // scroll to top
        this.getQueryView().getScrollable().getScroller().scrollTo(0, 0);

        Ext.Viewport.setActiveItem(this.getQueryView());
    }
});
