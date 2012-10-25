Ext.define("App.view.Query", {
    extend: 'Ext.Container',
    xtype: 'queryview',
    requires: ['Ext.dataview.List', 'App.model.Query'],

    config: {
        fullscreen: true,
        scrollable: 'vertical',
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
        }, {
            pseudo: 'coordinates'
        }, {
            xtype: 'list',
            itemTpl: '<div>{detail}</div>',
            selectedCls: '',
            emptyText: 'No query result',
            store: 'queryStore',
            onItemDisclosure: true,
            pinHeaders: true,
            ui: 'round',
            grouped: true,
            scrollable: false
        }]
    }
});
