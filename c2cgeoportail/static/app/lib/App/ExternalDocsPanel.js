/*
 */

Ext.namespace('App');

/**
 * Constructor: App.ExternalDocsPanel
 */
App.ExternalDocsPanel = function() {

    // Public

    Ext.apply(this, {

        /**
         * APIProperty: panel
         * The {Ext.Panel} instance. Read-only.
         */
        panel: null
    });

    var tpl = new Ext.XTemplate(
        '<p>',
        '<tpl for=".">',       // process the data.kids node
            '<p>{#}. <a href="{url}" target="_blank">{name}</a></p>',  // use current array index to autonumber
        '</tpl></p>'
    );

    // Main
    this.panel = new Ext.Panel({
        title: OpenLayers.i18n('External Documents'),
        html: tpl.apply(App.externalDocs),
        cls: 'external-documents'
    });

};

