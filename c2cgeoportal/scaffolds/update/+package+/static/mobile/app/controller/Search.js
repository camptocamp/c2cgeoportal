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

Ext.define('App.controller.Search', {
    extend: 'Ext.app.Controller',

    config: {
        refs: {
            searchField: 'searchfield[action=search]',
            searchView: {
                selector: 'searchview',
                xtype: 'searchview',
                autoCreate: true
            }
        },
        control: {
            searchField: {
                focus: function(field) {
                    // hide all items but search field so that it gets bigger
                    var toolbar = field.parent;
                    toolbar.items.each(function(item) {item.hide();});
                    field.show();
                },
                blur: function(field) {
                    var toolbar = field.parent;
                    toolbar.items.each(function(item) {item.show();});
                },
                action: function(field) {
                    this.redirectTo('search/' + encodeURIComponent(field.getValue()));
                    field.blur();
                }
            },
            searchView: {
                select: function(list, record) {
                    var f = new OpenLayers.Format.GeoJSON().read(record.raw)[0];
                    this.getApplication().getController('Main').recenterMap(f);
                    this.getApplication().getController('Main').setParams(f.attributes.params);
                },
                disclose: function(list, record) {
                    var f = new OpenLayers.Format.GeoJSON().read(record.raw)[0];
                    this.getApplication().getController('Main').recenterMap(f);
                    this.getApplication().getController('Main').setParams(f.attributes.params);
                }
            }
        },
        routes: {
            'search/:terms': 'showSearchResultView'
        }
    },

    //called when the Application is launched, remove if not needed
    launch: function(app) {

    },

    showSearchResultView: function(terms) {
        terms = decodeURIComponent(terms);
        var view = this.getSearchView();
        var animation = {type: 'cover', direction: 'up'};
        Ext.Viewport.animateActiveItem(view, animation);
        var store = view.getStore();
        store.getProxy().setExtraParams({
            'query': terms,
            'maxRows': 20
        });
        store.load();
    }
});
