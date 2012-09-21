Ext.define("App.view.Settings", {
    extend: 'Ext.Container',
    xtype: 'settingsview',

    config: {
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
            xtype: 'container',
            items: [{
                html: 
                    '<h1 class="title">Copyright</h1>' +
                    '<p>This map\'s data comes from OpenStreetMap and Camptocamp.org</p>'
            }]
        }]
    }
});
