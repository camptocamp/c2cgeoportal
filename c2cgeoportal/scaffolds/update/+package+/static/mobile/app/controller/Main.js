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
            },
            loginFormView: {
                selector: 'loginformview',
                xtype: 'loginformview',
                autoCreate: true
            },
            themesView: {
                selector: 'themesview',
                xtype: 'themesview',
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
            'button[action=loginform]': {
                tap: function() {
                    this.redirectTo('loginform');
                }
            },
            'button[action=login]': {
                tap: function() {
                    this.login();
                }
            },
            'button[action=logout]': {
                tap: function() {
                    this.logout();
                }
            },
            mainView: {
                longpress: function(view, bounds, map) {
                    this.queryMap(view, bounds, map);
                }
            },
            '#baselayer_switcher': {
                painted: function(cmp) {
                    var baseLayersStore = Ext.create('Ext.data.Store', {
                        model: 'App.model.Layer'
                    });
                    Ext.each(App.map.layers, function(layer) {
                        if (layer.isBaseLayer) {
                            baseLayersStore.add(layer);
                        }
                    });
                    cmp.setStore(baseLayersStore);

                    // listen to change event only once the store is set
                    cmp.on({
                        'change': function(select, newValue) {
                            App.map.setBaseLayer(App.map.getLayer(newValue));
                            this.redirectTo('');
                        }
                    });
                }
            },
            '#theme_switcher': {
                tap: function() {
                    this.redirectTo('themes');
                }
            },
            themesView: {
                itemtap: 'onThemeChange'
            }
        },
        routes: {
            '': 'showHome',
            'home': 'showHome',
            'layers': 'showLayers',
            'settings': 'showSettings',
            'themes': 'showThemes',
            'loginform': 'showLoginForm'
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

    showLoginForm: function() {
        var view = this.getLoginFormView();
        Ext.Viewport.setActiveItem(view);
    },

    showSettings: function() {
        var view = this.getSettingsView();
        Ext.Viewport.setActiveItem(view);
    },

    showThemes: function() {
        var view = this.getThemesView();
        Ext.Viewport.setActiveItem(view);
    },

    login: function() {
        this.getLoginFormView().submit();
    },

    logout: function() {
        window.location = App.logoutUrl;
    },

    recenterMap: function(f) {
        this.getMainView().recenterOnFeature(f);
        this.redirectTo('home');
    },

    setParams: function(params) {
        this.getMainView().getMap().layers.map(this.setLayerParams(params));
        this.getMainView().getMap().events.triggerEvent("changeparams", params);
    },

    setLayerParams: function(params) {
        return function(layer) {
            if (layer.setParams) {
                layer.setParams(params);
            }
            else if (layer.mergeNewParams) { // WMS or WMTS 
                layer.mergeNewParams(params); 
            }
        }
    },

    toArray: function(value) {
        return Ext.isArray(value) ? value : value.split(',');
    },

    queryMap: function(view, bounds, map) {
        var layers = [];

        // overlay layers
        for (var i=0; i<map.layers.length; i++) {
            var layer = map.layers[i];
            if (!layer.isBaseLayer && layer.visibility &&
                layer.CLASS_NAME != 'OpenLayers.Layer.Vector') {
                var layersParam = this.toArray(layer.params.LAYERS),
                    WFSTypes = this.toArray(layer.WFSTypes);
                for (var j=0; j<layersParam.length; j++) {
                    if (WFSTypes.indexOf(layersParam[j]) != -1) {
                        layers.push(layersParam[j]);
                    }
                }
            }
        }

        // currently displayed baseLayer
        if (map.baseLayer.WFSTypes) {
            layers = layers.concat(this.toArray(map.baseLayer.WFSTypes));
        }

        // launch query only if there are layers to query
        if (layers.length) {
            var p = [bounds, layers.join(',')];
            var joinedParams = p.join('-');
            joinedParams = encodeURIComponent(joinedParams);
            this.redirectTo('query/' + joinedParams);
        }
    },

    onThemeChange: function(list, index, target, record) {
        window.location = '?theme=' + record.get('name');
    }
});
