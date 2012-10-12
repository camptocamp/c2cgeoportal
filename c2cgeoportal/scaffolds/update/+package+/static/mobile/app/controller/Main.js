Ext.define('App.controller.Main', {
    extend: 'Ext.app.Controller',
    
    config: {
        refs: {
            mainView: 'mainview',
            layersView: 'layersview',
            settingsView: {
                selector: 'settingsview',
                xtype: 'settingsview',
                autoCreate: true
            }
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
            'button[action=settings]': {
                tap: function() {
                    this.redirectTo('settings');
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
            'layers': 'showLayers',
            'settings': 'showSettings'
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

    showSettings: function() {
        var view = this.getSettingsView();
        Ext.Viewport.setActiveItem(view);
    },

    recenterMap: function(f) {
        this.getMainView().recenterOnFeature(f);
        this.redirectTo('home');
    },

    queryMap: function(view, bounds, map) {
        var layers = [];

        // overlay layers
        for (var i=0; i<map.layers.length; i++) {
            var layer = map.layers[i];
            if (!layer.isBaseLayer && layer.visibility &&
                layer.CLASS_NAME != 'OpenLayers.Layer.Vector') {
                var layersParam = layer.params.LAYERS;
                for (var j=0; j<layersParam.length; j++) {
                    if (layer.WFSTypes.indexOf(layersParam[j]) != -1) {
                        layers.push(layersParam[j]);
                    }
                }
            }
        }

        // currently displayed baseLayer
        if (map.baseLayer.WFSTypes) {
            layers = layers.concat(map.baseLayer.WFSTypes);
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
