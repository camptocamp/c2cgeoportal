Ext.define('App.controller.Main', {
    extend: 'Ext.app.Controller',
    
    config: {
        refs: {
            mainView: 'mainview',
            layersView: 'layersview'
        },
        control: {
            'button[action=home]': {
                tap: function() {
                    this.redirectTo('home');
                }
            },
            'button[action=layers]': {
                tap: function() {
                    this.redirectTo('layers');
                }
            },
            mainView: {
                longpress: function(view, bounds, map) {
                    this.queryMap(view, bounds, map);
                }
            }
        },
        routes: {
            '': 'showHome',
            'home': 'showHome',
            'layers': 'showLayers'
        }
    },
    
    //called when the Application is launched, remove if not needed
    launch: function(app) {
        
    },

    showHome: function() {
        Ext.Viewport.setActiveItem(0);
    },

    showLayers: function() {
        var view = this.getLayersView();
        if (!view) {
            view = Ext.create('App.view.Layers');
            var store = Ext.create('Ext.data.Store', {
                model: 'App.model.Layer',
                data: this.getMainView().getMap().layers
            });
            view.setStore(store);
        }
        Ext.Viewport.setActiveItem(view);
    },

    recenterMap: function(record) {
        var f = record.raw;
        this.getMainView().recenterOnFeature(f);
        this.redirectTo('home');
    },

    queryMap: function(view, bounds, map) {
        var layers = [];
        for (var i=0; i<map.layers.length; i++) {
            var layer = map.layers[i];
            if (!layer.isBaseLayer && layer.visibility &&
                layer.CLASS_NAME != 'OpenLayers.Layer.Vector') {
                var layersParam = layer.params.LAYERS;
                for (var j=0; j<layersParam.length; j++) {
                    if (layer.WFSTypes.indexOf(layersParam[j])) {
                        layers.push(layersParam[j]);
                    }
                }
            }
        }
        // launch query only if there are layers to query
        if (layers.length) {
            var p = [bounds, layers.join(',')];
            var joinedParams = p.join('-');
            joinedParams = encodeURIComponent(joinedParams);
            this.redirectTo('query/' + joinedParams);
        }
    }
});
