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
