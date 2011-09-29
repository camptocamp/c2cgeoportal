/*
 * @include OpenLayers/Control/ZoomToMaxExtent.js
 * @include OpenLayers/Control/ZoomBox.js
 * @include OpenLayers/Control/ZoomOut.js
 * @include OpenLayers/Control/Navigation.js
 * @include OpenLayers/Control/NavigationHistory.js
 * @include OpenLayers/Handler/Path.js
 * @include OpenLayers/Handler/Polygon.js
 * @include OpenLayers/Control/Measure.js
 * @include OpenLayers/Layer/Vector.js
 * @include OpenLayers/Renderer/SVG.js
 * @include OpenLayers/Renderer/VML.js
 * @include OpenLayers/StyleMap.js
 * @include OpenLayers/Style.js
 * @include OpenLayers/Rule.js
 * @include OpenLayers/Handler.js
 * @include GeoExt/data/LayerStore.js
 * @include GeoExt/widgets/Action.js
 * @include GeoExt.ux/MeasureLength.js
 * @include GeoExt.ux/MeasureArea.js
 * @requires FeatureEditing/ux/widgets/FeatureEditingControler.js
 * @include FeatureEditing/ux/widgets/form/RedLiningPanel.js
 * @include App/FeaturePanel.js
 * @include GeoExt/widgets/WMSLegend.js
 * @include GeoExt/widgets/LegendPanel.js
 * @include GeoExt/widgets/LayerOpacitySlider.js
 * @include GeoExt/widgets/tree/WMSCapabilitiesLoader.js
 * @include App/Locator.js
 * @include App/Permalink.js
 * @include App/Search.js
 * @include App/Query.js
 * @include App/ToolButton.js
 * @include App/ToolWindow.js
 */

Ext.namespace('App');

/**
 * Constructor: App.Tools
 * Creates an {Ext.Toolbar} with tools. Use the "tbar" property to
 * get a reference to the Ext toolbar.
 *
 * Parameters:
 * map - {OpenLayers.Map} The map object.
 * layerStore - {GeoExt.data.LayerStore} The layerstore.
 * orthoLayer - {OpenLayers.Layer.WMS} The ortho layer.
 * events - {Ext.util.Observable} the application events manager.
 */
App.Tools = function(map, layerStore, orthoLayer, events, isApi) {

    // Private

    /**
     * Method: createBaselayerCombo
     * Create a combobox for the baselayer selection.
     *
     * Returns:
     * {Ext.form.ComboBox} The combobox.
     */
    var createBaselayerCombo = function() {

        // base layer store
        var store = new GeoExt.data.LayerStore({
            layers: map.getLayersBy("isBaseLayer", true)
        });

        var combo = new Ext.form.ComboBox({
            editable: false,
            hideLabel: true,
            width: 140,
            store: store,
            displayField: 'title',
            valueField: 'title',
            value: map.baseLayer.name,
            triggerAction: 'all',
            mode: 'local',
            listeners: {
                'select': function(combo, record, index) {
                    map.setBaseLayer(record.getLayer());
                }
            }
        });

        map.events.on({
            "changebaselayer": function(e) {
                combo.setValue(e.layer.name);
            }
        });

        return combo;
    };

    /**
     * Method: createOrthoLabel
     * Create the label for the ortho opacity clider.
     *
     * Returns:
     * {Ext.BoxComponent} The box containing the label.
     */
    var createOrthoLabel = function() {
        return new Ext.BoxComponent({
            html: ['<span class="tools-baselayer-label">',
                   OpenLayers.i18n('Tools.ortholabel'),
                   '</span>'].join('')
        });
    };

    /**
     * Method: createOpacitySlider
     * Create the slider for the Orthophoto
     *
     * Returns:
     * {Ext.BoxComponent} The opacity slider
     */
    var createOpacitySlider = function(orthoLayer, map) {
        var slider = new GeoExt.LayerOpacitySlider({
            width: 100,
            layer: orthoLayer,
            inverse: true,
            aggressive: true,
            changeVisibility: true,
            complementaryLayer: map.baseLayer,
            maxvalue: 100,
            style: "margin-right: 10px;"
        });
        map.events.register("changebaselayer", slider, function(e) { 
            slider.complementaryLayer = e.layer; 
            slider.complementaryLayer.setVisibility(!(orthoLayer.opacity == 1));
        });
        return slider;
    };

    /**
     * Method: createRedliningButton
     * Create the redlining button.
     *
     * Parameters:
     * tbar - {Ext.Toolbar} The window will be positioned
     *     relatively to this toolbar's parent.
     *
     * Returns:
     * {Ext.Button} The button.
     */
    var createRedliningButton = function(tbar) {

        /**
         * Method: deactivateRedlining
         * Deactivates all redlining controls
         */
        // See monkey patch (end of this file)
        var deactivateRedlining = function() {
            var actions = redliningPanel.controler.actions;
            for (var i=0; i < actions.length; i++) {
                if (actions[i].control) {
                    actions[i].control.deactivate();
                }
            }
        };

        /**
         * Property: redliningPanel
         */
        var redliningPanel = new GeoExt.ux.form.RedLiningPanel({
            map: map,
            layerOptions: {
                displayInLayerSwitcher: false
            },
            popupOptions: {
                unpinnable: false,
                draggable: true
            },
            selectControlOptions: {
                toggle: false,
                clickout: false
            },
            'export': false,
            'import': false,
            bodyStyle: 'display: none',
            border: false
        });

        /**
         * Prorperty: redliningWindow
         */
        var redliningWindow = new App.ToolWindow({
            width: 200, 
            items: [redliningPanel]
        });

        var button = new App.ToolButton(
            new Ext.Action({
                text: OpenLayers.i18n('Tools.redlining'),
                enableToggle: true,
                toggleGroup: map.id + '_tools',
                window: redliningWindow
            })
        );
        button.on({
            'toggle': function(button) {
                if (!button.pressed) {
                    deactivateRedlining();
                }
            }
        });

        return button;
    };

    /**
     * Method: createLegendButton
     * Create the legend button.
     *
     * Parameters:
     * tbar - {Ext.Toolbar} The print window will be positioned
     *     relatively to this toolbar's parent.
     *
     * Returns:
     * {Ext.Button} The button.
     */
    var createLegendButton = function(tbar) {

        var legendWin = new App.ToolWindow({
            width: 340,
            bodyStyle: 'padding: 5px',
            title: OpenLayers.i18n("Tools.legendwindowtitle"),
            border: false,
            layout: 'fit',
            autoHeight: false,
            height: 350,
            closeAction: 'hide',
            autoScroll: true,
            cls: 'legend toolwindow'
        });

        
        legendPanel = new GeoExt.LegendPanel({
            unstyled: true,
            autoScroll: true,
            defaults: {
                baseParams: {
                    FORMAT: 'image/png'
                }
            }
        });
        var legendPanelAdded = false

        // _gx_legendpanel should be available only when window is open
        legendWin.on({
            'show': function() {
                if (!legendPanelAdded) {
                    legendWin.add(legendPanel);
                    legendWin.doLayout();
                }
            }
        });

        return {
            legendPanel: legendPanel,
            toolButton: new App.ToolButton({
                text: OpenLayers.i18n("Tools.legendbuttontext"),
                tooltip: OpenLayers.i18n("Tools.legendbuttontooltip"),
                enableToggle: true,
                toggleGroup: map.id + '_tools',
                window: legendWin
            })
        };
    };

    /**
     * Method: createLoginButton
     * Create the login button.
     *
     * Returns:
     * {App.ToolButton} The button.
     */
    var createLoginButton = function() {
        var button = new Ext.Button({
            text:'Login',
            formBind: true,
            handler: submitForm
        });
        var loginForm = new Ext.FormPanel({
            labelWidth: 100,
            width: 230,
            unstyled: true,
            url: App.loginURL,
            defaultType: 'textfield',
            monitorValid: true,
            defaults: {
                enableKeyEvents: true,
                listeners: {
                    specialkey: function(field, el) {
                        if (el.getKey() == Ext.EventObject.ENTER) {
                            submitForm();
                        }
                    }
                }
            },
            items:[{
                fieldLabel: OpenLayers.i18n('Tools.username'),
                name: 'login',
                applyTo: 'login',
                width: 120,
                allowBlank: false
            }, {
                fieldLabel: OpenLayers.i18n('Tools.password'),
                name: 'password',
                applyTo: 'password',
                inputType: 'password',
                width: 120,
                allowBlank: false
            }, {
                xtype: 'box',
                ref: 'failureMsg',
                html: OpenLayers.i18n('Tools.authenticationFailure'),
                hidden: true
            }],
            buttons:[button]
        });

        function submitForm() {
            button.setIconClass('loading');
            loginForm.getForm().submit({
                method: 'POST',
                success:function() {
                    if (Ext.isIE) {
                        window.external.AutoCompleteSaveForm(loginForm.getForm().el.dom);
                    }
                    loginForm.getForm().el.dom.action = window.location.href;
                    loginForm.getForm().standardSubmit = true;
                    loginForm.getForm().submit();
                },
                failure:function(form, action) {
                    button.setIconClass('');
                    loginForm.getForm().reset();
                    loginForm.failureMsg.show();
                }
            });
        }

        /**
         * Property: loginWindow
         * {Ext.Window} The login window.
         */
        var loginWindow = new App.ToolWindow({
            width: 250,
            items: loginForm
        });
        loginWindow.render(Ext.getBody());

        var loginButton;
        if (App.user) {
            loginButton = [
                new Ext.Toolbar.TextItem({
                    text: OpenLayers.i18n('Tools.LoggedAs', {user : App.user})
                }),
                new Ext.Button({
                    text: OpenLayers.i18n('Tools.Logout'),
                    handler: function() {
                        Ext.Ajax.request({
                            url: App.logoutURL,
                            success: function() {
                                window.location.href = window.location.href;
                            }
                        })
                    }
                })
            ];
        } else {
            loginButton = new App.ToolButton({ 
                text: OpenLayers.i18n("Tools.Login"),
                enableToggle: true,
                toggleGroup: 'mode',
                window: loginWindow
            });
        }
        return loginButton;
    };


    /**
     * Method: createTbar
     * Create the toolbar.
     *
     * Returns:
     * {Ext.Toolbar} The toolbar.
     */
    var createTbar = function() {
        var tbar = new Ext.Toolbar(), items = [];

        // zoom buttons
        items.push(new GeoExt.Action({
            control: new App.ZoomToMaxExtent(),
            map: map,
            iconCls: 'maxExtent',
            tooltip: OpenLayers.i18n("Tools.maxextentactiontooltip")
        }));
        items.push(new GeoExt.Action({
            control: new OpenLayers.Control.ZoomBox(),
            map: map,
            toggleGroup: map.id + '_tools',
            allowDepress: true,
            iconCls: 'mapZoomIn'
        }));
        items.push(new GeoExt.Action({
            control: new OpenLayers.Control.ZoomOut(),
            map: map,
            iconCls: 'mapZoomOut'
        }));
        items.push('-');

        // navigation history buttons
        var history = new OpenLayers.Control.NavigationHistory();
        map.addControl(history);
        items.push(new GeoExt.Action({
            control: history.previous,
            disabled: true,
            iconCls: 'mapHistoryPrevious'
        }));
        items.push(new GeoExt.Action({
            control: history.next,
            disabled: true,
            iconCls: 'mapHistoryNext'
        }));

        if (!isApi) {
            // permalink button
            items.push((new App.Permalink()).action);
        }
        items.push('-');

        // measure buttons
        items.push((new App.Locator(map, {
            toggleGroup: map.id + '_tools',
            tooltip: OpenLayers.i18n("Tools.measurepositionactiontooltip"),
            iconCls: 'mapMeasurePosition'
        })).action);
        var sketchSymbolizers = {
            "Point": {
                pointRadius: 4,
                graphicName: "square",
                fillColor: "white",
                fillOpacity: 1,
                strokeWidth: 1,
                strokeOpacity: 1,
                strokeColor: "#E53C42"
            },
            "Line": {
                strokeWidth: 2,
                strokeOpacity: 1,
                strokeColor: "#E53C42"
            },
            "Polygon": {
                strokeWidth: 2,
                strokeOpacity: 1,
                strokeColor: "#E53C42",
                fillColor: "white",
                fillOpacity: 0.3
            }
        };
        var styleMap = new OpenLayers.StyleMap({
            "default": new OpenLayers.Style(null, {
                rules: [new OpenLayers.Rule({symbolizer: sketchSymbolizers})]
            })
        });
        items.push(new GeoExt.ux.MeasureLength({
            map: map,
            toggleGroup: map.id + '_tools',
            tooltip: OpenLayers.i18n("Tools.measurelengthactiontooltip"),
            styleMap: styleMap
        }));
        items.push(new GeoExt.ux.MeasureArea({
            map: map,
            toggleGroup: map.id + '_tools',
            tooltip: OpenLayers.i18n("Tools.measureareaactiontooltip"),
            styleMap: styleMap
        }));
        items.push('-');

        if (!isApi) {
            // query button
            items.push((new App.Query({
                events: events,
                map: map,
                tbar: tbar,
                toggleGroup: map.id + '_tools'
            })).action);
            items.push('-');
        }

        // search
        var combo = (new App.Search(map)).combo;
        items.push(combo);

        items.push('->');
        // redlining
        items.push(createRedliningButton(tbar));
        // legend button
        legend = createLegendButton(tbar)
        items.push(legend.toolButton);

        if (!isApi) {
            items.push('-');
            items.push(createLoginButton());
        }

        items.push('-');
        items.push(new GeoExt.Action({
            iconCls: 'help',
            tooltip: OpenLayers.i18n("Tools.helpactiontooltip"),
            handler: function() {
                window.open(App["HelpURL"]);
            }
        }));

        tbar.add.apply(tbar, [items]);
        return {
            legendPanel: legend.legendPanel,
            bar: tbar
        };
    };

    /**
     * Method: createMapBar
     * Creates the map toolbar.
     *
     * Returns:
     * {Ext.Toolbar} The toolbar.
     */
    var createMapBar = function() {
       var mapbar = new Ext.Toolbar({
           cls: 'opacityToolbar'
       }), items = [];
       // baselayer selection
       items.push(createOrthoLabel());
       items.push(createOpacitySlider(orthoLayer, map));
       items.push(createBaselayerCombo());
       mapbar.add(items);
       return mapbar;
    };    
    
    // Public

    Ext.apply(this, {

        /**
         * APIProperty: tbar
         * {Ext.Toolbar} The top toolbar instance. Read-only.
         */
        tbar: null,
 	  	 
        /**
         * APIProperty: mapbar
         * {Ext.Toolbar} The toolbar instance to put in the map. Read-only.
         */
        mapbar: null

    });

    // Main

    tbar = createTbar();
    this.legendPanel = tbar.legendPanel;
    this.tbar = tbar.bar;
    this.mapbar = createMapBar();
};

// monkey patch
GeoExt.ux.FeatureEditingControler.prototype.reactivateDrawControl = Ext.emptyFn;

App.ZoomToMaxExtent = OpenLayers.Class(OpenLayers.Control.ZoomToMaxExtent, {
    trigger: function() {
        if (this.map) {
            if (App['extent']) {
                this.map.zoomToExtent(OpenLayers.Bounds.fromArray(App['extent']));
            } else {
                this.map.zoomToMaxExtent();
            }
        }
    },

    CLASS_NAME: "App.ZoomToMaxExtent"
});
