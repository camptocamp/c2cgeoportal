Ext.define('App.model.Query', {
    extend: 'Ext.data.Model',

    config: {
        fields: [
            {
                name: 'detail',
                mapping: 'properties',
                convert: function(value, record) {
                    var detail = [],
                        attributes = record.raw.attributes;
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
                    return detail.join('');
                }
            },
            {name: 'type'}
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
