Ext.define("App.view.Search", {
    extend: 'Ext.dataview.List',
    xtype: 'searchview',
    requires: ['Ext.dataview.List', 'App.model.Search'],

    config: {
        fullscreen: true,
        itemTpl: '<div>{name}</div>',
        selectedCls: '',
        emptyText: 'No search result',
        store: 'searchStore',
        onItemDisclosure: true,
        pinHeaders: true,
        ui: 'round',
        grouped: true,
        items: [{
            docked: 'top',
            xtype: 'toolbar',
            items: [{
                xtype: 'spacer'
            }, {
                xtype: 'button',
                iconCls: 'home',
                iconMask: true,
                action: 'home'
            }]
        }]
    }
});
