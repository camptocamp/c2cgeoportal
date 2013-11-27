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
                this.setMap(map);
                // apply saved state
                var state = this.getState();
                if (state) {
                    view.setCenter(state.lonlat);
                    view.setZoom(state.zoom);
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
        var state = localStorage.getItem(this.getMap().id + '-position');
        if (state) {
            var items = state.split(',');
            return {
                lonlat: items.slice(0, 2),
                zoom: items[2]
            };
        }
    },

    applyState: function(state) {
        var key = this.getMap().id + '-position',
            value = [state.lonlat.lon, state.lonlat.lat, state.zoom].join(',');

        localStorage.setItem(key, value);
    }
});
