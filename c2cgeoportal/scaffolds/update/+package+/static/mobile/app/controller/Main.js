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

Ext.define('App.controller.Main', {
    extend: 'Ext.app.Controller',

    config: {
        overlay: null,
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
                'change': function(select, newValue) {
                    App.map.setBaseLayer(App.map.getLayer(newValue));
                    this.redirectTo('');
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
        // To deal with params, the following methods are available:
        // * `getParams`: returns all params
        // * `setParams`: used to update the values of some params
        //
        // Three OpenLayers Map events are also available:
        // * `changeparams`: launched with the changed params values
        // * `changeparamsready`: launched when the application is ready to
        //   receive `dochangeparams` events
        // * `dochangeparams`: used to call for `setParams` without knowing
        //   the current object.
        //
        // Events are passed through the map in order to be able to create an
        // OpenLayers Controller that uses the params without any dependencies
        // on Sencha Touch, required by a project component.
        this.params = {};
        this.map = this.getMainView().getMap();
        this.map.events.register('addlayer', this, function(event){
            this.setLayerParams(this.params)(event.layer);
        });
        this.map.events.register('dochangeparams', this, function(event){
            this.setParams(event.params);
        });
        this.map.events.triggerEvent('changeparamsready');
    },

    showHome: function() {
        var animation = {type: 'reveal', direction: 'down'};
        if (Ext.Viewport.getActiveItem() == this.getLoginFormView()) {
            animation = {type: 'fade'};
        }
        Ext.Viewport.animateActiveItem(0, animation);
        var view = this.getLayersView();
        var mainView = this.getMainView();
        view.getStore().setData(mainView.getMap().layers);
    },

    showLayers: function() {
        var view = this.getLayersView();
        if (!view) {
            view = Ext.create('App.view.Layers');
            view.getStore().setData(this.getMainView().getMap().layers);
        }
        var animation;
        if (Ext.Viewport.getActiveItem() == this.getMainView()) {
            animation = {type: 'cover', direction: 'up'};
        } else if (Ext.Viewport.getActiveItem() == this.getThemesView()) {
            animation = {type: 'slide', direction: 'right'};
        }
        Ext.Viewport.animateActiveItem(view, animation);
    },

    showLoginForm: function() {
        var view = this.getLoginFormView();
        var animation = {type: 'fade'};
        Ext.Viewport.animateActiveItem(view, animation);
    },

    showSettings: function() {
        var view = this.getSettingsView();
        var animation = {type: 'cover', direction: 'up'};
        Ext.Viewport.animateActiveItem(view, animation);
    },

    showThemes: function() {
        var view = this.getThemesView();
        var animation = {type: 'slide', direction: 'left'};
        Ext.Viewport.animateActiveItem(view, animation);
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

    getParams: function() {
        return this.params;
    },

    setParams: function(params) {
        Ext.apply(this.params, params);
        this.map.layers.map(this.setLayerParams(params));
        this.map.events.triggerEvent("changeparams", {
            params: params
        });
    },

    setLayerParams: function(params) {
        return function(layer) {
            if (layer.setParams) {
                layer.setParams(params);
            }
            else if (layer.mergeNewParams) { // WMS or WMTS
                layer.mergeNewParams(params);
            }
        };
    },

    toArray: function(value) {
        return Ext.isArray(value) ? value : value.split(',');
    },

    // get the list of queryable layers given a list of displayed WMS layers
    getChildLayers: function(ollayer, params) {
        var result = [],
            allLayers = ollayer.allLayers;
        Ext.each(params, function(p) {
            Ext.each(allLayers, function(layer) {
                if (layer.name == p) {
                    if (layer.childLayers) {
                        Ext.each(layer.childLayers, function(item) {
                            result.push(item.name);
                        });
                    } else {
                        result.push(layer.name);
                    }
                }
            });
        });
        return result;
    },

    queryMap: function(view, bounds, map) {
        var layers = [];

        // overlay
        var overlay = this.getOverlay();
        var layersParam = this.toArray(overlay.params.LAYERS),
            WFSTypes = this.toArray(App.WFSTypes);
        // Ensure that we query the child layers in case of groups
        layersParam = this.getChildLayers(overlay, layersParam);
        for (var j=0; j<layersParam.length; j++) {
            if (WFSTypes.indexOf(layersParam[j]) != -1) {
                layers.push(layersParam[j]);
             }
        }

        // currently displayed baseLayer
        if (map.baseLayer.WFSTypes) {
            layers = layers.concat(this.toArray(map.baseLayer.WFSTypes));
        }

        // launch query only if there are layers or raster to query
        if (layers.length || App.raster) {
            var layers = encodeURIComponent(layers.join('-'));
            var bounds = encodeURIComponent(bounds.toArray().join('-'));
            this.redirectTo(['query', bounds, layers].join('/'));
        }
    },

    onThemeChange: function(list, index, target, record) {
        var map = this.getMainView().getMap(),
            theme = record.get('name'),
            overlay = this.getOverlay();
        if (overlay) {
            map.removeLayer(overlay);
        }
        this.loadTheme(theme);
        this.getLayersView().getStore().setData(map.layers);

        this.redirectTo('layers');
    },

    loadTheme: function(theme) {
        if (!theme) {
            if (App.themes && App.themes.length > 0) {
                App.theme = theme = App.themes[0].name;
            }
            else if (console) {
                console.log("No themes are displayed in mobile for the curent role");
            }
        }
        Ext.each(App.themes, function(t) {
            if (t.name == theme) {
                if (App.map.getLayerIndex(this.getOverlay()) != -1) {
                    App.map.removeLayer(this.getOverlay());
                }
                var overlay = new OpenLayers.Layer.WMS(
                    'overlay',
                    App.wmsUrl,
                    {
                        // layers to display at startup
                        layers: t.layers,
                        transparent: true
                    },{
                        singleTile: true,
                        // list of available layers
                        allLayers: t.allLayers
                    }
                );
                App.map.addLayer(overlay);
                this.setOverlay(overlay);
                App.theme = theme;
                App.map.events.triggerEvent('themechange');
                return false;
            }
        }, this);
    }
});
