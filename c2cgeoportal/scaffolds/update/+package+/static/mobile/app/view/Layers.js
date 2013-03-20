Ext.define("App.view.Layers", {
    extend: 'Ext.form.Panel',
    xtype: 'layersview',

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
        }],
        defaults: {
            xtype: 'checkboxfield',
            labelWidth: '80%'
        }
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
                    var checkbox = this.add({
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
