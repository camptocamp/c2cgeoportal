/**
 * Copyright (c) 2011-2013 by Camptocamp SA
 *
 * CGXP is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * CGXP is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with CGXP. If not, see <http://www.gnu.org/licenses/>.
 */

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
            title: OpenLayers.i18n('layer_switcher.background'),
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
            title: OpenLayers.i18n('layer_switcher.data_layers'),
            id: 'overlays',
            items: [{
                xtype: 'button',
                id: 'theme_switcher',
                text: ' ',
                iconCls: "right",
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
        themesStore.add(App.themes);

        var store = Ext.create('Ext.data.Store', {
            model: 'App.model.Layer',
            listeners: {
                refresh: this.dataChanged,
                scope: this
            }
        });
        this.setStore(store);

        var currentTheme = themesStore.find('name', App.theme);
        if (currentTheme == -1) {
            currentTheme = 0;
        }

        if (App.themes.length > 1) {
            this.setButtonText(App.theme);
        }
        else {
            this.down('#theme_switcher').hide();
        }

        var baseLayerSwitcher = this.down('#baselayer_switcher');
        var baseLayersStore = Ext.create('Ext.data.Store', {
            model: 'App.model.Layer'
        });
        Ext.each(App.map.layers, function(layer) {
            if (layer.isBaseLayer) {
                baseLayersStore.add(layer);
            }
        });
        baseLayerSwitcher.setStore(baseLayersStore);
        if (baseLayersStore.getAllCount() <= 1) {
            baseLayerSwitcher.parent.hide();
        }
        baseLayerSwitcher.setValue(App.map.baseLayer.id);
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

    setButtonText: function(theme) {
        this.down('#theme_switcher').setText(
            OpenLayers.i18n('theme_switcher.prefix') +
            OpenLayers.i18n(theme)
        );
    },

    dataChanged: function(store) {
        // set theme switcher name
        this.setButtonText(App.theme);
        var overlaysContainer = this.down('#overlays');
        // remove previous layers from list
        while (overlaysContainer.getAt(1)) {
            overlaysContainer.removeAt(1);
        }
        store.each(function(record) {
            var layer = record.raw;
            if (!layer.isBaseLayer && layer.allLayers &&
                    layer instanceof OpenLayers.Layer.WMS) {
                var allLayers = layer.allLayers,
                    layersParam = layer.params.LAYERS ?
                        this.toArray(layer.params.LAYERS) : [],
                    i, l;
                for (i = allLayers.length - 1; i >= 0; --i) {
                    l = allLayers[i].name;
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
