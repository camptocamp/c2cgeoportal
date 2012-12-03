Ext.define('App.view.Login', {
    extend: 'Ext.Component',
    xtype: 'login',
    initialize: function() {
        var tpl = App.info.username ? 'authenticatedTpl' : 'unauthenticatedTpl';
        this.setTpl(OpenLayers.i18n(tpl));
        this.setData({
            username: App.info.username,
            logoutUrl: App.logoutUrl
        });
    }
});
