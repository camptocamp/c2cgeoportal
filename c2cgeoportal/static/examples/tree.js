var map, tree;
Ext.onReady(function() {
    Ext.QuickTips.init();



    map = new OpenLayers.Map('olmap');
    map.addLayers([
        new OpenLayers.Layer('fake', {isBaseLayer: true})
    ]); 
    //map.setCenter(new OpenLayers.LonLat(10, 45), 4);
    map.zoomToExtent(new OpenLayers.Bounds(-155.146484,33.134766,-65.146484,78.134766));

    tree = new App.LayerTree({
        width: 250,
        height: 400,
        //wmsURL: 'http://vmap0.tiles.osgeo.org/wms/vmap0?',
        wmsURL: 'http://www2.dmsolutions.ca/cgi-bin/mswms_gmap',
        map: map,
        themes: App.themes,
        defaultThemes: App.default_themes
    });
    var themesSelector = new App.ThemeSelector(
        App.themes, 
        tree
    );
    themesSelector.button.render('tree');
    tree.render('tree');

    //tree.loadTheme(App.themes.local[0]);

    Ext.state.Manager.setProvider(
        new Ext.state.Provider()
    );
    // Registers a statechange listener to update the value
    // of the permalink text field.
    Ext.state.Manager.getProvider().on({
        statechange: function(provider) {
        }
    });
});
