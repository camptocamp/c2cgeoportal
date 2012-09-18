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

    checkChange: function() {
        this.getFieldsAsArray().forEach(function(field) {
            var record = field.getRecord();
            var map = record.get('map');
            var checked = field.getChecked();
            if (record.raw.isBaseLayer && checked) {
                map.setBaseLayer(record.raw);
            }
            record.raw.setVisibility(checked);
        });
    },

    overlayCheckChange: function(field) {
        var record = field.getRecord();
        var layer = record.raw;
        var layersParam = layer.params.LAYERS || [];
        var name = field.getName();
        var checked = field.getChecked();
        if (checked) {
            layersParam.push(name);
        } else {
            OpenLayers.Util.removeItem(layersParam, name);
        }
        layer.mergeNewParams({'LAYERS': layersParam});
        layer.setVisibility(layersParam.length);
    },

    updateStore: function(store) {
        store.each(function(record) {
            var layer = record.raw;
            if (!layer.isBaseLayer &&
                layer instanceof OpenLayers.Layer.WMS) {
                var allLayers = layer.allLayers,
                    layersParam = layer.params.LAYERS,
                    len = allLayers.length,
                    i, l;
                for (i=0; i<len; i++) {
                    l = allLayers[i];
                    this.add({
                        label: OpenLayers.i18n(l),
                        name: l,
                        checked: layersParam.indexOf(l) != -1,
                        listeners: {
                            check: this.overlayCheckChange,
                            uncheck: this.overlayCheckChange,
                            scope: this
                        }
                    }).setRecord(record);
                }
            }
        }, this);
    }
});
