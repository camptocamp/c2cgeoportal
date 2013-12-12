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

Ext.define('App.plugin.StatefulMap', {
    alias: 'plugin.statefulmap',

    config: {
        map: null,
        state: null
    },

    init: function(view) {
        if (view) {
            view.on('setmap', function(view, map) {
                var main = App.app.getController('Main');
                this.setMap(map);
                // apply saved state
                var state = this.getState();
                if (state.theme) {
                    App.theme = state.theme;
                    main.loadTheme(state.theme);
                }
                if (state.bgLayer) {
                    map.setBaseLayer(
                        map.getLayersBy('layer', state.bgLayer)[0]
                    );
                }
                if (state.layers) {
                    var overlay = main.getOverlay();
                    overlay.mergeNewParams({layers: state.layers});
                    Ext.each(App.themes, function(theme){
                        if (theme.name !== App.theme) {
                            return;
                        }
                        var layers = state.layers.map(function(layer) {
                            return { "name": layer };
                        });
                        theme.allLayers = (theme.allLayers || []);
                        Ext.each(layers, function(l) {
                            if (l.name == "") {
                                return;
                            }
                            if (theme.allLayers.filter(function(a) {
                                    return a.name == l.name;
                                }).length==0) {
                                theme.allLayers.push(l);
                            }
                        });
                        overlay.allLayers = theme.allLayers;
                        overlay.layers = state.layers;
                        return false;
                    });
                    main.getLayersView().getStore().setData(map.layers);
                }
                if (state.lonlat) {
                    map.setCenter(state.lonlat, state.zoom);
                }
                map.events.on({
                    moveend: this.update,
                    changebaselayer: this.update,
                    changelayer: this.update,
                    removelayer: this.update,
                    addlayer: this.update,
                    themechange: this.update,
                    scope: this
                });
            }, this);
        }
    },

    update: function() {
        var center = this.getMap().getCenter();
        var main = App.app.getController('Main');
        this.setState({
            lonlat: [center.lon, center.lat],
            zoom: this.getMap().getZoom(),
            theme: App.theme,
            bgLayer: this.getMap().baseLayer.layer,
            layers: main.getOverlay().params.LAYERS
        });
    },

    getState: function() {
        var q= Ext.Object.fromQueryString(window.location.search),
            state = {
                theme: q.theme,
                bgLayer: q.baselayer_ref
            };
        Ext.iterate(q, function(key, value) {
            if ('tree_group_layers_' === key.substr(0, 18)) {
                state.layers = state.layers || [];
                state.layers.push.apply(state.layers, value.split(','));
            }
        });
        if (q.map_x && q.map_y) {
            state.lonlat = [ q.map_x, q.map_y ];
            state.zoom = q.map_zoom;
        }
        return state;
    },

    applyState: function(state) {
        var layers = (state.layers.join && state.layers[0] != '') ?
            state.layers.join(',') : state.layers,
            params,
            qs;

        var params = {
            theme: state.theme,
            baselayer_ref: state.bgLayer,
            map_x: state.lonlat[0],
            map_y: state.lonlat[1],
            map_zoom: state.zoom
        };
        if (state.layers) {
            params.tree_layers = (state.layers.join) ?
                    state.layers.join(',') : state.layers
        }

        var qs = Ext.Object.toQueryString(params);
        if (history.replaceState) {
            history.replaceState(null, '',
                location.pathname + '?' + qs
            );
        }
    }
});
