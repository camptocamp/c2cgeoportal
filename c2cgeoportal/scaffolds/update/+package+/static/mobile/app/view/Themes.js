Ext.define("App.view.Themes", {
    extend: 'Ext.List',
    xtype: 'themesview',

    config: {
        items: [
            {
                docked: 'top',
                xtype: 'toolbar',
                title: 'Thèmes',
                items: [{
                    ui: 'back',
                    text: 'back',
                    listeners: {
                        tap: function() {
                            history.back();
                        }
                    }
                }]
            }
        ],
        itemTpl: new Ext.XTemplate(
            '<div class="theme">',
                '<img src="{icon}" />',
                '<div class="info"><b>{[OpenLayers.i18n(values.name)]}</b></div>',
            '</div>'
        ),
        store: 'themesStore',
        disableSelection: true
    }
});
