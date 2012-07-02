Ext.define("App.view.Query", {
    extend: 'Ext.dataview.List',
    xtype: 'queryview',
    requires: ['Ext.dataview.List', 'App.model.Query'],

    config: {
        fullscreen: true,
        itemTpl: '<div>{detail}</div>',
        selectedCls: '',
        emptyText: 'No query result',
        store: 'queryStore',
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
