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

Ext.define('App.model.Query', {
    extend: 'Ext.data.Model',

    config: {
        fields: [
            {
                name: 'detail',
                mapping: 'properties',
                convert: function(value, record) {
                    if (typeof record.raw.attributes == 'object') {
                        var detail = App.getDetail ? App.getDetail(record.raw) : null;
                        if (!detail) {
                            detail = []
                            var attributes = record.raw.attributes;
                            detail.push('<table class="detail">');
                            for (var k in attributes) {
                                if (attributes.hasOwnProperty(k) && attributes[k]) {
                                    detail = detail.concat([
                                        '<tr>',
                                        '<th>',
                                        OpenLayers.i18n(k),
                                        '</th>',
                                        '<td>',
                                        OpenLayers.String.format(attributes[k], App),
                                        '</td>',
                                        '</tr>'
                                    ]);
                                }
                            }
                            detail.push('</table>');
                            detail = detail.join('');
                        }
                        return detail;
                    }
                    return record.raw.detail;
                }
            },
            {name: 'type'},
            {name: 'disclosure'}
        ]
    }
});

Ext.create('Ext.data.Store', {
    storeId: 'queryStore',
    model: 'App.model.Query',
    grouper: {
        groupFn: function(record) {
            return OpenLayers.i18n(record.get('type'));
        }
    }
});
