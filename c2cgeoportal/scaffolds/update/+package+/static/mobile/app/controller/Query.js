Ext.define('App.controller.Query', {
    extend: 'Ext.app.Controller',
    
    config: {
        protocol: null,
        refs: {
            queryView: {
                selector: 'queryview',
                xtype: 'queryview',
                autoCreate: true
            }
        },
        control: {
            queryView: {
                select: function(list, record) {
                    this.getApplication().getController('Main').recenterMap(record.raw);
                },
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
        var store = this.getQueryView().getStore();
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

        Ext.Viewport.setActiveItem(this.getQueryView());
    }
});
