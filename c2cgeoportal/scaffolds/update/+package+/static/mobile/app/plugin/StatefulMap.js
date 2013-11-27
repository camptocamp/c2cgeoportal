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
                        theme.allLayers = state.layers.map(function(layer) {
                            return { "name": layer };
                        });
                        overlay.allLayers = theme.allLayers;
                        return false;
                    });
                    main.getLayersView().getStore().setData(map.layers);
                }
                if (state.lonlat) {
                    map.setCenter(state.lonlat, state.zoom);
                }
                map.events.on({
                    moveend: this.moveend,
                    scope: this
                });
            }, this);
        }
    },

    moveend: function() {
        this.setState({
            lonlat: this.getMap().getCenter(),
            zoom: this.getMap().getZoom()
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
        var key = this.getMap().id + '-position',
            value = [state.lonlat.lon, state.lonlat.lat, state.zoom].join(',');

        localStorage.setItem(key, value);
    }
});
