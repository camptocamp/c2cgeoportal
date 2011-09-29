/**
 * @include FeatureEditing/ux/data/FeatureEditingDefaultStyleStore.js
 * @include Styler/ux/LayerStyleManager.js
 * @include Styler/ux/widgets/StyleSelectorComboBox.js
 */

GeoExt.ux.form.FeaturePanel.prototype.initMyItems = function() {
    var oItems, oGroup, feature, field, oGroupItems;

    // todo : for multiple features selection support, remove this...
    if (this.features.length != 1) {
        return;
    } else {
        feature = this.features[0];
    }
    oItems = [];
    oGroupItems = [];
    oGroup = {
        id: this.attributeFieldSetId,
        xtype: 'fieldset',
        title: OpenLayers.i18n('Attributes'),
        layout: 'form',
        collapsible: true,
        autoHeight: this.autoHeight,
        autoWidth: this.autoWidth,
        defaults: this.defaults,
        defaultType: this.defaultType
    };

    if (feature.isLabel) {
        oGroupItems.push({
            name: 'name',
            fieldLabel: OpenLayers.i18n('name'),
            id: 'name',
            value: feature.attributes['name']
        });
    } else {
        var styleStore = new Ext.data.SimpleStore(
            GeoExt.ux.data.getFeatureEditingDefaultStyleStoreOptions());
        styleStore.sort('name');
        var styler = new GeoExt.ux.LayerStyleManager(
            new GeoExt.ux.StyleSelectorComboBox({
                store: styleStore,
                comboBoxOptions: {
                    emptyText: OpenLayers.i18n("select a color..."),
                    fieldLabel: OpenLayers.i18n('color'),
                    editable: false,
                    typeAhead: true,
                    selectOnFocus: true
                }
        }), {});
        styler.setCurrentFeature(this.features[0]);

        oGroupItems.push(styler.createLayout().comboBox);
    }

    oGroup.items = oGroupItems;

    oItems.push(oGroup);

    Ext.apply(this, {items: oItems});
};

GeoExt.ux.form.FeaturePanel.prototype.getActions = function() {
    if (!this.closeAction) {
        this.closeAction = new Ext.Action({
            handler: function() {
                this.controler.triggerAutoSave();
                if(this.controler.popup) {
                    this.controler.popup.close();
                }
                this.controler.reactivateDrawControl();
            },
            scope: this,
            text: OpenLayers.i18n('Close')
        });
    }

    return [this.deleteAction, '->', this.closeAction];
};
