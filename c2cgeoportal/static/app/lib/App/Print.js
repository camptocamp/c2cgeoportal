/*
 * @include GeoExt/widgets/Action.js
 * @include GeoExt/data/PrintProvider.js
 * @include GeoExt/plugins/PrintProviderField.js
 * @include GeoExt.ux/SimplePrint.js
 * @include OpenLayers/Feature/Vector.js
 * @include OpenLayers/Geometry/Polygon.js
 * @include OpenLayers/Layer/Vector.js
 * @include OpenLayers/Renderer/SVG.js
 * @include OpenLayers/Renderer/VML.js
 * @include OpenLayers/Control/TransformFeature.js
 */
Ext.namespace('App');

/**
 * Constructor: App.Print
 * Creates a {GeoExt.ux.SimplePrint} internally. Use the "printPanel"
 * property to get a reference to this print panel.
 *
 * Parameters:
 * mapPanel - {GeoExt.MapPanel} The map panel the print panel is connect to.
 * options - {Object} Options passed to the {GeoExt.ux.SimplePrint}.
 */
App.Print = function(mapPanel, legendPanel, resultPanel, options) {

    // Private

    /**
     * Property: printPanel
     * {GeoExt.ux.SimplePrint} The print panel.
     */
    var printPanel = null;


    // Public

    Ext.apply(this, {
        
        /**
         * APIProperty: printPanel
         * {GeoExt.ux.SimplePrint} The print panel. Read-only.
         */
        printPanel: null
    });

    // Main

    // create a print provider
    var printProvider = new GeoExt.data.PrintProvider({
        url: App.printURL,
        baseParams: {
            url: App.printURL
        },
        listeners: {
            beforedownload: function(pp, url) {
                if (Ext.isIE) {
                    var win = new Ext.Window({
                        width: 200,
                        cls: 'pdf-window',
                        items: [
                            {
                                html: OpenLayers.i18n('Print.Ready')
                            },
                            {
                                xtype: 'button',
                                text: OpenLayers.i18n('Print.Download'),
                                handler: function() {
                                    window.open(url);
                                    win.hide();
                                }
                            }
                        ]
                    });
                    win.show();
                }
                else if (Ext.isOpera) {
                    // Make sure that Opera don't replace the content tab
                    // with the pdf
                    window.open(url);
                } else {
                    // This avoids popup blockers for all other browsers
                    window.location.href = url;
                }
                return false;
            }
        }
    });
    printProvider.on('beforeencodelayer', function(printProvider, layer) {
        if (layer instanceof OpenLayers.Layer.Vector) {
            var features = [];
            // reviews the layer features to remove the wrong ones
            // (because they make the print service crash)
            for (var i = 0, n = layer.features.length; i < n; i++) {
                var f = layer.features[i];
                var b = f.geometry.bounds;

                // removes 0-length lines
                if (f.geometry instanceof OpenLayers.Geometry.LineString &&
                    (!b || (b.getWidth() == 0 && b.getHeight() == 0))) {
                    continue;
                }

                // removes flat polygons
                if ((f.geometry instanceof OpenLayers.Geometry.Polygon ||
                    f.geometry instanceof OpenLayers.Geometry.MultiPolygon) &&
                    f.geometry.getArea() == 0) {
                    continue;
                }

                features.push(f);
            }
            if (features.length == 0) {
                return false;
            }
            layer.features = features;
        }
        return true;
    });
    printProvider.on('encodelayer', function(printProvider, layer, encodedLayer) {
        var apply = false;
        if (layer.ref == 'plan_color') {
            encodedLayer.layers = App["encodedLayers"]["plan_color"];
            encodedLayer.format = 'image/png';
            apply = true;
        }  
        if (layer.ref == 'plan') {
            encodedLayer.layers = App["encodedLayers"]["plan"];
            encodedLayer.format = 'image/png';
            apply = true;
        }
        if (layer.ref == 'ortho') {
            encodedLayer.layers = App["encodedLayers"]["ortho"];
            encodedLayer.format = 'image/jpeg';
            apply = true;
        }
        if (apply) {
            encodedLayer.baseURL =  App["mapserverproxyURL"];
            encodedLayer.type =  'WMS';
            delete encodedLayer.dimensions;
            delete encodedLayer.formatSuffix;
            delete encodedLayer.layer;
            delete encodedLayer.matrixSet;
            delete encodedLayer.maxExtent;
            delete encodedLayer.params;
            delete encodedLayer.requestEncoding;
            delete encodedLayer.resolutions;
            delete encodedLayer.style;
            delete encodedLayer.tileOrigin;
            delete encodedLayer.tileSize;
            delete encodedLayer.version;
            delete encodedLayer.zoomOffset;
            encodedLayer.singleTile = true;
        }
        if (encodedLayer) {
            encodedLayer.useNativeAngle = true;
        }
    });
    printProvider.on('beforeprint', function(printProvider, map, pages, options) {
        // need to define the table object even for page0 as java expects it
        pages[0].customParams = {col0: '', table:{data:[{col0: ''}], columns:['col0']}};
        pages[0].customParams.showMap = true;
        pages[0].customParams.showScale = true;
        pages[0].customParams.showAttr = false;
        pages[0].customParams.showNorth = true;
        pages[0].customParams.showScalevalue = true;
        pages[0].customParams.showMapframe = true;
        pages[0].customParams.showMapframeQueryresult = false;
        // new blank page, if query results
        var printExport = resultPanel.printExport();
        // TODO, implement paging in case of too many result to display on only one page
        if (printExport.table.data.length > 0 && printExport.table.data[0].col0 != '') {
            var page1 = new GeoExt.data.PrintPage({
                printProvider: printProvider
            });
            page1.center = pages[0].center.clone();
            page1.customParams = printExport;
            page1.customParams.showMap = false;
            page1.customParams.showScale = false;
            page1.customParams.showAttr = true;
            page1.customParams.showNorth = false;
            page1.customParams.showScalevalue = false;
            page1.customParams.showMapframe = false;
            page1.customParams.showMapframeQueryresult = true;
            pages[1] = page1;
        } else {
          // remove page 1 if is exists (user printed a page with query result before clearing the query result)
          if (pages[1]) {
              pages.pop();
          }          
        }
    });

    // create the print panel
    options = Ext.apply({
        mapPanel: mapPanel,
        map: mapPanel.map,
        printOptions: {'legend': legendPanel},
        bodyStyle: 'padding: 10px',
        printProvider: printProvider,
        items: [{
            xtype: 'textfield',
            name: 'title',
            fieldLabel: OpenLayers.i18n("Print.titlefieldlabel"),
            value: OpenLayers.i18n("Print.titlefieldvalue"),
            plugins: new GeoExt.plugins.PrintProviderField(),
            autoCreate: {tag: "input", type: "text", size: "45", maxLength: "45"}
        }, {
            xtype: 'textarea',
            name: 'comment',
            fieldLabel: OpenLayers.i18n("Print.commentfieldlabel"),
            value: OpenLayers.i18n("Print.commentfieldvalue"),
            plugins: new GeoExt.plugins.PrintProviderField(),
            autoCreate: {tag: "textarea", maxLength: "100"}
        }],
        comboOptions: {
            editable: false
        },
        dpiText: OpenLayers.i18n("Print.dpifieldlabel"),
        scaleText: OpenLayers.i18n("Print.scalefieldlabel"),
        rotationText:  OpenLayers.i18n("Print.rotationfieldlabel"),
        printText: OpenLayers.i18n("Print.printbuttonlabel"),
        creatingPdfText: OpenLayers.i18n("Print.waitingmessage")
    }, options); 
    printPanel = new GeoExt.ux.SimplePrint(options);

    printProvider.on('printexception', function(printProvider, response) {
        printPanel.busyMask.hide();
        Ext.Msg.alert(
            OpenLayers.i18n('Print.failuretitle'),
            OpenLayers.i18n('Print.failuremsg')
        );
    });

    // the print panel auto-shows the print extent when
    // the capabilities are loaded. We work around that
    // by listening to loadcapabilities and hiding the
    // extent when the capabilities are loaded.
    printProvider.on({
        'loadcapabilities': function() {
            printPanel.hideExtent();
        }
    });
    printProvider.loadCapabilities();

    // make the print panel public
    this.printPanel = printPanel;

    this.printPanel.on('expand', function() {
        this.printPanel.printExtent.fitPage();
    }, this);
};
