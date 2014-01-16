Ext.define("App.view.Settings", {
    extend: 'Ext.Container',
    xtype: 'settingsview',
    requires: [
        'App.view.Login'
    ],

    config: {
        scrollable: 'vertical',
        items: [{
            docked: 'top',
            xtype: 'toolbar',
            items: [{
                xtype: 'spacer'
            }, {
                xtype: 'button',
                text: OpenLayers.i18n('close'),
                action: 'home'
            }]
        }, {
            xtype: 'container',
            cls: 'settings',
            items: [{
                xtype: 'login'
            }, {
                xtype: 'component',
                html:
                    '<h1 class="title">Copyright</h1>' +
                    'Base Layer: Data CC-By-SA by <a href="http://openstreetmap.org/">OpenStreetMap</a>'
            }]
        }]
    }
});
