/**
 * Copyright (c) 2011-2014 by Camptocamp SA
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

Ext.define('App.model.Search', {
    extend: 'Ext.data.Model',

    config: {
        fields: [
            {name: 'name', mapping: 'properties.label'},
            {name: 'layer_name', mapping: 'properties.layer_name'},
            {name: 'params', mapping: 'properties.params'}
        ]
    }
});

Ext.create('Ext.data.Store', {
    storeId: 'searchStore',
    model: 'App.model.Search',
    grouper: {
        groupFn: function(record) {
            return OpenLayers.i18n(record.get('layer_name'));
        }
    },
    proxy: {
        // FIXME: is JsonP required?
        type: 'jsonp',
        url: App.searchUrl,
        reader: {
            type: 'json',
            rootProperty: 'features'
        }
    }
});
