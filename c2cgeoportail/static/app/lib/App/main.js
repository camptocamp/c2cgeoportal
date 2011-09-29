/*
 * @include App/Map.js
 * @include App/ThemeSelector.js
 * @include App/LayerTree.js
 * @include App/Print.js
 * @include App/QueryBuilder.js
 * @include App/globals.js
 * @include App/ResultsPanel.js
 * @include App/ExternalDocsPanel.js
 */

/*
 * This file represents the application's entry point. 
 * OpenLayers and Ext globals are set, and the page
 * layout is created.
 */

window.onload = function() {

    /*
     * Initialize the application.
     */
    App.setGlobals();
    
    var events = new Ext.util.Observable();
    var map = new App.Map({
        region: "center",
        // the initial map extent
        extent: new OpenLayers.Bounds(658960, 238880, 671720, 251640) // old version: 662000, 244000, 665000, 246000
    }, events);
    var mapPanel = map.mapPanel;

    var resultsPanel = new App.ResultsPanel(mapPanel.map, events, {
        region: "south",
        height: 160,
        split: true,
        collapseMode: "mini"
    }).panel;
    
    var querierPanel = new App.QueryBuilder(events, {
        title: OpenLayers.i18n("querier"),
        map: mapPanel.map,
        hidden: App.user ? false : true
    }).panel;
    
    var headerPanel = new Ext.Panel({
        region: 'north',
        contentEl: 'header-out'
    });
    var layerTreePanel = new App.LayerTree({
        header: false,
        flex: 1,
        autoScroll: true,
        map: mapPanel.map,
        wmsURL: App.mapserverproxyURL,
        themes: App.themes,
        defaultThemes: App.default_themes
    });
    var themeSelector = new App.ThemeSelector(
        App.themes,
        layerTreePanel
    );
    var layersPanel = {
        title: OpenLayers.i18n("layertree"),
        layout: 'vbox',
        layoutConfig: {
            align: 'stretch'
        },
        items: [{
            xtype: 'container',
            style: 'padding: 3px;',
            items: [themeSelector.button]
        },
            layerTreePanel
        ]
    };

    var printPanel = (new App.Print(mapPanel, map.legendPanel, resultsPanel, {
        title: OpenLayers.i18n("print"),
        labelAlign: 'top',
        defaults: {
            anchor:'100%'
        }
    })).printPanel;

    // the viewport
    var viewport = new Ext.Viewport({
        layout: "border",
        items: [
            headerPanel,
            mapPanel,
            resultsPanel,
            { 
                region: "west",
                layout: "accordion",
                width: 300,
                minWidth: 300,
                split: true,
                collapseMode: "mini",
                border: false,
                defaults: {width: 300},
                items: [layersPanel, querierPanel, printPanel]
            }
        ]
    });


    resultsPanel.on('show', function() {
        viewport.doLayout();
    });

    // remove loading message
    Ext.get('loading').remove();
    Ext.fly('loading-mask').fadeOut({
        remove:true
    });
};

