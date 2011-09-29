/*
 * @include GeoExt/widgets/tree/LayerContainer.js
 * @include GeoExt/widgets/tree/LayerLoader.js
 * @include GeoExt/plugins/TreeNodeComponent.js
 * @include GeoExt/widgets/LayerOpacitySlider.js
 * @include GeoExt/widgets/tips/LayerOpacitySliderTip.js
 * @include GeoExt/widgets/grid/FeatureSelectionModel.js
 * @include OpenLayers/Filter/Comparison.js
 * @include OpenLayers/StyleMap.js
 * @include OpenLayers/Rule.js
 * @include OpenLayers/Feature/Vector.js
 * @include OpenLayers/Control/SelectFeature.js
 */

Ext.namespace('App');

App.ResultsPanel = function(map, events, uiOptions) {

    /*
     * Private
     */

    var tabpan = null;
    var currentGrid = null;
    var gridByType = {};
    var textItem;

    var getProp = function(key, def) {
        var result = OpenLayers.i18n(key);
        return result === key ? def : result;
    }
    var comma = getProp('csv.comma', ',');
    var quote = getProp('csv.quote', '"');

    // http://tools.ietf.org/html/rfc4180
    var csvExport = function() {
        if (tabpan.activeTab) {
            var csv = [];
            var records = currentGrid.getSelectionModel().getSelections();

            if (records.length === 0) {
                records = currentGrid.getStore().getRange();
            }
            if (records.length === 0) {
                return;
            }
            Ext.each(records, function(r) {
                var attributes = r.getFeature().attributes;
                var properties = [];
                for (prop in attributes) {
                    if (attributes.hasOwnProperty(prop)) {
                        properties.push(quote + attributes[prop].replace(quote, quote+quote) + quote);
                    }
                }
                csv.push(properties.join(comma));
            });

            Ext.Ajax.request({
                url: App["csvURL"],
                method: 'POST',
                params: {
                    name: currentGrid.title,
                    csv: csv.join('\n')
                },
                form: dummy_form,
                isUpload: true
            });
        }
    };

    /** 
     * Export for print.
     * Columns titles will be stored on 'col1', 'col2', ... of the page.
     * The dataset name is 'table '.
     * The columns names will be 'col1', 'col2', ....
     */
    var printExport = function() {
        var results = {col0: '', table:{data:[{col0: ''}], columns:['col0']}};
        if (tabpan.activeTab && currentGrid) {
            var records = currentGrid.getSelectionModel().getSelections();
            if (records.length === 0) {
                records = currentGrid.getStore().getRange();
            }
            if (records.length === 0) {
                return results;
            }
            var firstRow = true;
            Ext.each(records, function(r) {
                var attributes = r.getFeature().attributes;
                var index = 0;
                var raw = {};
                if (firstRow) {
                    results.table.columns = [];
                    results.table.data = [];
                }
                for (prop in attributes) {
                    if (attributes.hasOwnProperty(prop)) {
                        var id = 'col' + index;
                        raw[id] = attributes[prop];
                        index++;
                        if (index > 9) {
                            break;
                        }
                        if (firstRow) {
                            results[id] = OpenLayers.i18n(prop);
                            results.table.columns.push(id);
                        }
                    }
                }
                firstRow = false;
                results.table.data.push(raw);
            });
        }
        return results;
    };
    
    
    var getCount = function() {
        if (!currentGrid) {
            return '';
        }
        var count = currentGrid.getStore().getCount();
        var plural = (count>1) ? "s" : "";
        return (count == App.MAX_FEATURES) ?
            OpenLayers.i18n("ResultsPanel.max_features_msg")+' ('+App.MAX_FEATURES+')':
            count+" "+OpenLayers.i18n("ResultsPanel.result"+plural);
        
    };

    /*
     * Main
     */

    // a ResultsPanel object has its own vector layer, which
    // is added to the map once for good
    var vectorLayer = new OpenLayers.Layer.Vector(
        OpenLayers.Util.createUniqueID("c2cgeoportal"), {
            displayInLayerSwitcher: false,
            alwaysInRange: true
    });
    map.addLayer(vectorLayer);

    events.on('queryopen', function() {
    });
 
    events.on('queryclose', function() {
        control && control.deactivate();
    });
   
    events.on('querystarts', function() {
        if (currentGrid !== null) {
            currentGrid.getSelectionModel().clearSelections();
        }
        currentGrid = null;
        vectorLayer.destroyFeatures();
        if (tabpan !== null) {
            tabpan.items.each(function (item) {
                tabpan.hideTabStripItem(item);
            });
            tabpan.doLayout();
        }
    });

    var control;
    events.on('queryresults', function(features) {
        // if no feature do nothing
        if (!features || features.length == 0) {
            return;
        }

        var currentType = {}, feature;
        for (var i = 0, len = features.length ; i < len ; i++) {
            feature = features[i];
            if (!feature.geometry && feature.bounds) {
                feature.geometry = feature.bounds.toGeometry();
            }

            feature.style = {display: 'none'};
            currentType[feature.type] = true;

            if (!control) {
                control = new OpenLayers.Control.SelectFeature(vectorLayer, {
                    toggle: true,
                    multiple: true,
                    multipleKey: (Ext.isMac ? "metaKey" : "ctrlKey")
                });
                map.addControl(control);
                control.handlers.feature.stopDown = false;
            } else {
                control.activate();
            }

            if (gridByType[feature.type] === undefined) {
                var fields = [];
                var columns = [];
                for (var attribute in feature.attributes) {
                    fields.push({name: attribute, type: 'string'});
                    columns.push({header: OpenLayers.i18n(attribute), dataIndex: attribute});
                }

                var store = new GeoExt.data.FeatureStore({
                    layer: vectorLayer,
                    fields: fields
                });

            
                var grid = new Ext.grid.GridPanel({
                    store: store,
                    viewConfig: {
                        // we add an horizontal scroll bar in case 
                        // there are too many attributes to display:
                        forceFit: (columns.length < 9)
                    },
                    colModel: new Ext.grid.ColumnModel({
                        defaults: {
                            sortable: true
                        },
                        columns: columns
                    }),
                    sm: new GeoExt.grid.FeatureSelectionModel({
                        selectControl: control,
                        singleSelect: false
                    }),
                    title: OpenLayers.i18n(feature.type)
                });
                grid.getSelectionModel().on('rowdeselect', function (model, index, record) {
                    record.getFeature().style = {display: 'none'};
                });
                grid.getSelectionModel().on('rowselect', function (model, index, record) {
                    record.getFeature().style = OpenLayers.Feature.Vector.style['default'];
                    record.getFeature().style.strokeWidth = 4;
                });
                grid.on('rowdblclick', function(gclickGrid, index) {
                    var feature = store.getAt(index).getFeature();
                    if (feature.bounds) {
                        var center = feature.bounds.getCenterLonLat();
                    } else if (feature.geometry) {
                        var centroid = feature.geometry.getCentroid();
                        center = new  OpenLayers.LonLat(centroid.x, centroid.y);
                    }
                    feature.layer.map.setCenter(center);
                });
                // task to fix an ext bug ...
                var task = new Ext.util.DelayedTask(function() {
                    var sm = currentGrid.getSelectionModel();
                    sm.clearSelections();
                    sm.selectFirstRow();
                });
                grid.on('render', function(renderGrid) {
                    if (currentGrid != null) {
                        currentGrid.getSelectionModel().clearSelections();
                    }
                    currentGrid = renderGrid
                    task.delay(200);
                });
                gridByType[feature.type] = grid;
                tabpan.add(grid);
            }
            else {
                var grid = gridByType[feature.type];
                tabpan.unhideTabStripItem(grid);
            }
        }
        vectorLayer.addFeatures(features);
        for (type in currentType) {
            gridByType[type].getStore().filterBy(function(record) {
                return record.getFeature().type === type && record.getFeature().layer;
            });
        }
        for (type in gridByType) {
            if (currentType[type]) {
                var firstType = type;
                continue;
            }
        }
        tabpan.setActiveTab(gridByType[firstType].id);
        currentGrid = tabpan.getActiveTab();
        textItem.setText(getCount());
        currentGrid.getSelectionModel().selectFirstRow();
        tabpan.setVisible(true);
        tabpan.expand();
        tabpan.doLayout();
    });
    
    

    textItem = new Ext.Toolbar.TextItem({
        text: ''
    }); 
    var dummy_form = Ext.DomHelper.append(document.body, {tag : 'form'});
    tabpan = new Ext.TabPanel(Ext.apply({
        plain: true,
        enableTabScroll: true,
        listeners: {
            "expand": function() {
                vectorLayer.setVisibility(true);
            },
            "collapse": function() {
                vectorLayer.setVisibility(false);
            }
        },
        bbar: [
            new Ext.SplitButton({
                text: OpenLayers.i18n('ResultsPanel.select'),
                handler: function() {
                    var sm = currentGrid.getSelectionModel();
                    sm.selectAll();
                }, // handle a click on the button itself
                menu: new Ext.menu.Menu({
                    items: [
                        {text: OpenLayers.i18n('ResultsPanel.select.all'), handler: function() {
                            var sm = currentGrid.getSelectionModel();
                            sm.selectAll();
                        }},
                        {text: OpenLayers.i18n('ResultsPanel.select.none'), handler: function() {
                            var sm = currentGrid.getSelectionModel();
                            sm.clearSelections();
                        }},
                        {text: OpenLayers.i18n('ResultsPanel.select.toggle'), handler: function() {
                            var sm = currentGrid.getSelectionModel();
                            var recordsToSelect = [];
                            currentGrid.getStore().each(function(record) {
                                if (!sm.isSelected(record)) {
                                    recordsToSelect.push(record);
                                }
                                return true;
                            });
                            sm.clearSelections();
                            sm.selectRecords(recordsToSelect);
                        }}
                    ]
                })
            }),
            {
                text: OpenLayers.i18n('ResultsPanel.actions'),
                //iconCls: 'user',
                menu: {
                    xtype: 'menu',
                    plain: true,
                    items: [{
                        text: OpenLayers.i18n('ResultsPanel.actions.zoomToSelection'), 
                        handler: function() {
                            var sm = currentGrid.getSelectionModel();
                            var bbox = new OpenLayers.Bounds();
                            Ext.each(sm.getSelections(), function(r){
                                bbox.extend(r.getFeature().geometry.getBounds());
                            });
                            if (bbox.getWidth() + bbox.getHeight() > 0) {
                                map.zoomToExtent(bbox.scale(1.05));
                            }
                        }
                    }, {
                        text: OpenLayers.i18n('ResultsPanel.actions.csvSelectionExport'), 
                        handler: csvExport
                    }]
                }
            } ,'->', textItem, '-',{
                text: OpenLayers.i18n('ResultsPanel.clearAll'),
                handler: function() {
                    vectorLayer.destroyFeatures();
                    textItem.setText('');
                    tabpan.setVisible(false);
                    tabpan.ownerCt.doLayout();
                }
            }
        ]
    }, uiOptions));

    tabpan.setVisible(false);
    tabpan.on('tabchange', function(tabPanel, tab) {
        if (currentGrid != null) {
            currentGrid.getSelectionModel().clearSelections();
        }
        currentGrid = tab;
        if (currentGrid != null) {
            currentGrid.getSelectionModel().selectFirstRow();
            textItem.setText(getCount());
        }
    });

    this.panel = tabpan;
    this.panel.printExport = printExport;    
};

