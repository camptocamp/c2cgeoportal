Ext.define('App.view.Login', {
    extend: 'Ext.Container',
    xtype: 'login',
    config: {
        layout: {
            type: 'vbox',
            align: 'left'
        }
    },
    initialize: function() {
        if (App.info) {
            var items;
            if (!App.info.username) {
                items = [{
                    xtype: 'button',
                    text: OpenLayers.i18n('loginButtonText'),
                    iconCls: 'lock_closed',
                    iconMask: true,
                    action: 'loginform'
                }];
            } else {
                items = [{
                    xtype: 'component',
                    tpl: OpenLayers.i18n('welcomeText'),
                    data: {username: App.info.username}
                }, {
                    xtype: 'button',
                    text: OpenLayers.i18n('logoutButtonText'),
                    iconCls: 'lock_open',
                    iconMask: true,
                    action: 'logout'
                }];
            }
            this.setItems(items);
        }
    }
});
