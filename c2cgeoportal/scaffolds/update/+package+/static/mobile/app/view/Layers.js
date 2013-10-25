Ext.define("App.view.Layers", {
    extend: 'Ext.form.Panel',
    xtype: 'layersview',

    requires: [
        'Ext.form.FieldSet'
    ],

    config: {
        store: null,
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
            xtype: 'fieldset',
            title: 'Fond',
            items: [{
                xtype: 'selectfield',
                id: 'baselayer_switcher',
                displayField: 'name',
                valueField: 'id',
                defaultPhonePickerConfig: {
                    cancelButton: OpenLayers.i18n('layer_switcher.cancel'),
                    doneButton: OpenLayers.i18n('layer_switcher.done')
                }
            }]
        }, {
            xtype: 'fieldset',
            title: 'Couches de données',
            id: 'overlays',
            items: [{
                xtype: 'button',
                id: 'theme_switcher',
                text: ' ',
                iconCls: "code3",
                iconMask: true,
                iconAlign: "right"
            }],
            defaults: {
                xtype: 'checkboxfield',
                labelWidth: '80%',
                labelWrap: true
            }
        }]
    },

    initialize: function() {
        this.callParent(arguments);

        var themesStore = Ext.create('Ext.data.Store', {
            model: 'App.model.Theme',
            id: 'themesStore'
        });
        this.setStore(themesStore);
        themesStore.add(App.themes);

        var queryParams = OpenLayers.Util.getParameters();
        var currentTheme = themesStore.find('name', queryParams.theme);
        if (currentTheme == -1) {
            currentTheme = 0;
        }
        this.down('#theme_switcher').setText(
            OpenLayers.i18n('theme_switcher.prefix') +
            OpenLayers.i18n(themesStore.getAt(currentTheme).get('name'))
        );
    },

    toArray: function(value) {
        return Ext.isArray(value) ? value : value.split(',');
    },

    overlayCheckChange: function(field) {
        var record = field.getRecord();
        var layer = record.raw;
        var layersParam = layer.params.LAYERS ?
            this.toArray(layer.params.LAYERS) : [];
        var name = field.getName();
        var checked = field.getChecked();
        if (checked) {
            layersParam.push(name);
        } else {
            OpenLayers.Util.removeItem(layersParam, name);
        }
        layer.setVisibility(layersParam.length !== 0);
        layer.mergeNewParams({'LAYERS': layersParam});
    },

    updateStore: function(store) {
        var overlaysContainer = this.down('#overlays');
        store.each(function(record) {
            var layer = record.raw;
            if (!layer.isBaseLayer &&
                layer instanceof OpenLayers.Layer.WMS) {
                var allLayers = this.toArray(layer.allLayers),
                    layersParam = layer.params.LAYERS ?
                        this.toArray(layer.params.LAYERS) : [],
                    i, l;
                for (i = allLayers.length - 1; i >= 0; --i) {
                    l = allLayers[i];
                    var checkbox = overlaysContainer.add({
                        label: OpenLayers.i18n(l),
                        name: l,
                        checked: layersParam.indexOf(l) != -1,
                        listeners: {
                            check: this.overlayCheckChange,
                            uncheck: this.overlayCheckChange,
                            scope: this
                        }
                    });
                    checkbox.on({
                        element: 'label',
                        tap: Ext.bind(function(checkbox) {
                            checkbox.setChecked(!checkbox.isChecked());
                        }, null, [checkbox])
                    });
                    checkbox.setRecord(record);
                }
            }
        }, this);
    }
});
