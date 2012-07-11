Ext.define('App.model.Search', {
    extend: 'Ext.data.Model',

    config: {
        fields: [
            {name: 'name', mapping: 'properties.label'},
            {name: 'layer_name', mapping: 'properties.layer_name'}
        ]
    }
});

Ext.create('Ext.data.Store', {
    storeId: 'searchStore',
    model: 'App.model.Search',
    groupField: 'layer_name',
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
