Ext.define("App.view.Permalink", {
    extend: 'Ext.Container',
    xtype: 'map_permalink',
    requires: [
        'Ext.field.Field'
    ],

    config: {
        cls: 'settings',
        items: [{
            xtype: 'textfield',
            label: OpenLayers.i18n('permalink'),
            id: 'permalink'
        }]
    },

    initialize: function() {
        this.callParent(arguments);

        this.on('painted', this.registerSelect, this, {
            single: true
        });
        this.on('painted', function() {
            this.down('#permalink').setValue(
                window.location.href
            );
        }, this);
    },

    registerSelect: function() {
        this.down('#permalink').element.down('.x-input-text').on({
            'focus' : {
                fn : function() {
                    this.dom.selectionStart = 0;
                    this.dom.selectionEnd = this.dom.value.length;
                },
                delay : 100
            }
        });
    }

});
