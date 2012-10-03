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
            cls: 'settings',
            items: [{
                xtype: 'component',
                html: 
                    '<h1 class="title">Copyright</h1>' +
                    'Base Layer: Data CC-By-SA by <a href="http://openstreetmap.org/">OpenStreetMap</a><br />' +
                    'Overlay Layers: Courtesy of <a href="http://camptocamp.org/">Camptocamp.org</a>'
            }]
        }]
    }
});
