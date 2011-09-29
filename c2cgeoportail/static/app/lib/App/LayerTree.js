/*
 * @requires GeoExt/widgets/tree/LayerNode.js
 * @include GeoExt/widgets/tree/LayerParamNode.js
 * @include GeoExt/widgets/tree/TreeNodeUIEventMixin.js
 * @include GeoExt/plugins/TreeNodeActions.js
 * @include GeoExt/plugins/TreeNodeComponent.js
 * @include GeoExt/widgets/LayerOpacitySlider.js
 * @include App/TreeNodeLoading.js
 * @include App/TreeNodeComponent.js
 * @include App/TreeNodeTriStateUI.js
 */

Ext.namespace('App');

App.LayerTree = Ext.extend(Ext.tree.TreePanel, {
    
    baseCls: 'layertree',
    enableDD: false,
    rootVisible: false,
    useArrows: true,

    /**
     * Property: themes
     * The initialConfig of themes
     */
    themes: null,

    /**
     * Property: defaultThemes
     * The themes to load on start up 
     */
    defaultThemes: null,

    /**
     * Property: wmsURL
     * The url to the WMS service
     */
    wmsURL: null,

    /** private: property[stateEvents]
     *  ``Array(String)`` Array of state events
     */
    stateEvents: ["addgroup", "ordergroup", "removegroup", "themeopacitychange", "layervisibilitychange"],

    stateId: 'tree',

    /**
     * Property: actionsPlugin
     */

    initComponent: function() {
        this.root = {
            nodeType: 'async',
            children: [],
            expanded: true
        };

        this.actionsPlugin = new GeoExt.plugins.TreeNodeActions({
            listeners: {
                action: this.onAction
            }
        });
        this.plugins = [
            this.actionsPlugin,
            new GeoExt.plugins.TreeNodeComponent(),
            new App.TreeNodeComponent({
                divCls: "legend-component",
                configKey: "legend"
            }),
            new App.TreeNodeLoading()
        ];
        var layerNodeUI = Ext.extend(Ext.tree.TreeNodeTriStateUI, new GeoExt.tree.TreeNodeUIEventMixin());
        this.loader = new Ext.tree.TreeLoader({
            uiProviders: {
                layer: layerNodeUI,
                'default': Ext.tree.TreeNodeTriStateUI
            }
        });
        App.LayerTree.superclass.initComponent.call(this, arguments);
        this.on({
            "beforeexpandnode": function(node) {
                node.eachChild(this.checkVisibility);
            },
            scope: this
        });
        this.getSelectionModel().on({
            "beforeselect": function() {
                return false;
            }
        });
        
        this.addEvents(
            /** private: event[addgroup]
             *  Fires after a theme is added. 
             */
            "addgroup",

            /** private: event[removegroup]
             *  Fires after a theme is removed.
             */
            "removegroup",

            /** private: event[layervisibilitychange]
             *  Fires after a checkbox state changes
             */
            "layervisibilitychange",

            /** private: event[themeopacitychange]
             *  Fires after the theme opacity changes. 
             */
            "themeopacitychange",

            /** private: event[ordergroup]
             *  Fires after the themes order is changed.
             */
            "ordergroup"
        );
        this.on('checkchange', function(node, checked) {
            this.fireEvent("layervisibilitychange");
            if (!this.changing) {
                this.changing = true;
                node.cascade(function(node){
                    node.getUI().toggleCheck(checked);
                });
                node.bubble(function(node){
                    if (node.parentNode) {
                        node.getUI().updateCheck();
                    }
                });
                this.changing = false;
            }
        }, this);
        this.changing = false;

        this.on('click', function(node) {
            node.getUI().toggleCheck(!node.getUI().isChecked());
        });

        this.on('afterrender', function() {
            Ext.each(this.defaultThemes, function(theme) {
                this.loadTheme(this.findThemeByName(theme));
            }, this);
        }, this);

        this.map.events.on({
            'zoomend': function() {
                this.getRootNode().cascade(this.checkInRange);
            },
            scope: this
        });
        this.on({
            "expandnode": function(node) {
                node.eachChild(this.checkInRange);
            }
        });
    },

    /**
     * Method: addGroup
     * Adds a layer group and its layers
     *
     * Parameters:
     * {Object} The group config object
     */
    addGroup: function(group) {
        function addNodes(children, parentNode) {
            var checkedNodes = group.layer.params.LAYERS;
            Ext.each(children, function(item) {
                var nodeConfig = {
                    text: OpenLayers.i18n(item.name),
                    iconCls: 'no-icon',
                    loaded: true,
                    checked: checkedNodes.indexOf(item.name) != -1,
                    uiProvider: 'default',
                    minResolutionHint: item.minResolutionHint,
                    maxResolutionHint: item.maxResolutionHint
                };
                if (!item.children) {
                    this.addMetadata(item, nodeConfig);
                    this.addLegend(item, nodeConfig);
                    this.addScaleAction(item, nodeConfig);
                    Ext.apply(nodeConfig, {
                        nodeType: 'gx_layerparam',
                        leaf: true,
                        layer: item.layer,
                        allItems: group.allLayers,
                        item: item.name,
                        param: 'LAYERS',
                        uiProvider: 'layer'
                    });
                }
                var node = parentNode.appendChild(nodeConfig);
                if (item.children) {
                    addNodes.call(this, item.children, node);
                }
            }, this);
        }
        
        function updateMoveUp(el) { 
            var isFirst = this.isFirst();
            if (isFirst && !this._updating &&
            this.nextSibling &&
            this.nextSibling.hidden === false) {
                this._updating = true; // avoid recursion
                var next = this.nextSibling;
                if (next) {
                    this.ownerTree.actionsPlugin.updateActions(next);
                }
                delete this._updating;
            }
            if (isFirst) {
                el.addClass('disabled');
            } else {
                el.removeClass('disabled'); 
            }
        }

        function updateMoveDown(el) { 
            var isLast = this.isLast();
            if (isLast && !this._updating &&
            this.previousSibling &&
            this.previousSibling.hidden === false) {
                this._updating = true; // avoid recursion
                var previous = this.previousSibling;
                if (previous) {
                    this.ownerTree.actionsPlugin.updateActions(previous);
                }
                delete this._updating;
            }
            if (isLast) {
                el.addClass('disabled'); 
            } else {
                el.removeClass('disabled'); 
            }
        }

        var groupNode = this.root.insertBefore({
            text: OpenLayers.i18n(group.name),
            groupId: group.name,
            nodeType: 'app_layer',
            iconCls: 'no-icon',
            cls: 'x-tree-node-theme',
            loaded: true,
            uiProvider: 'layer', 
            checked: false,
            layer: group.layer,
            component: this.getOpacitySlider(group),
            actions: [{
                action: "opacity",
                qtip: OpenLayers.i18n("Tree.opacity")
            }, {
                action: "up",
                qtip: OpenLayers.i18n('Tree.moveup'),
                update: updateMoveUp
            }, {
                action: "down",
                qtip: OpenLayers.i18n('Tree.movedown'),
                update: updateMoveDown
            }, {
                action: "delete",
                qtip: OpenLayers.i18n("Tree.delete")
            }]
        }, this.root.firstChild);
        addNodes.call(this, group.children, groupNode);
        this.fireEvent('addgroup');
        groupNode.expand(true, false);
        groupNode.collapse(true, false);
        groupNode.cascade(this.checkInRange);
    },

    /**
     * Method: addLegend
     * Adds the action and the legend component to a node config
     */
    addLegend: function(item, nodeConfig) {
        var config = {};
        nodeConfig.actions = nodeConfig.actions || [];
        if (item.icon) {
            config.icon = item.icon;
        }
        if (item.legend) {
            if (item.legendRule) { // there is only one class in the mapfile layer
                // we use a rule so that legend shows the icon only (no label) 
                config.icon = this.getLegendGraphicUrl(item.layer, item.name, item.legendRule);
            } else  {
                var src = (item.legendImage) ?
                    item.legendImage :
                    this.getLegendGraphicUrl(item.layer, item.name); 

                config.legend = new Ext.Container({
                    items: [{
                        xtype: 'box',
                        html: '<img src="' + src + '" />'
                    }],
                    listeners: {
                        render: function(cmp) {
                            cmp.getEl().setVisibilityMode(Ext.Element.DISPLAY);
                            cmp.getEl().hide.defer(1, cmp.getEl(), [false]);
                        }
                    }
                });

                nodeConfig.actions.push({
                    action: "legend",
                    qtip: OpenLayers.i18n("Tree.showhidelegend")
                });
            }
        }
        if (config.icon) {
            config.iconCls = "x-tree-node-icon-wms";
        }
        Ext.apply(nodeConfig, config);
    },

    /**
     * Method: getLegendGraphicUrl
     * Helper to build the getLegendGraphic request URL
     */
    getLegendGraphicUrl: function(layer, layerName, rule) {
        var layerNames = [layer.params.LAYERS].join(",").split(",");

        var styleNames = layer.params.STYLES &&
                             [layer.params.STYLES].join(",").split(",");
        var idx = layerNames.indexOf(layerName);
        var styleName = styleNames && styleNames[idx];

        var url = layer.getFullRequestString({
            REQUEST: "GetLegendGraphic",
            WIDTH: null,
            HEIGHT: null,
            EXCEPTIONS: "application/vnd.ogc.se_xml",
            LAYER: layerName,
            LAYERS: null,
            STYLE: (styleName !== '') ? styleName: null,
            STYLES: null,
            SRS: null,
            FORMAT: layer.format,
            RULE: rule
        });

        // add scale parameter - also if we have the url from the record's
        // styles data field and it is actually a GetLegendGraphic request.
        if(this.useScaleParameter === true &&
                url.toLowerCase().indexOf("request=getlegendgraphic") != -1) {
            var scale = layer.map.getScale();
            url = Ext.urlAppend(url, "SCALE=" + scale);
        }
        
        return url;
    },

    /**
     * Method: addMetadata
     * Adds the action for the metadata
     */
    addMetadata: function(item, nodeConfig) {
        if (item.metadataUrls) {
            nodeConfig.actions = nodeConfig.actions || [];
            nodeConfig.actions.push({
                action: "metadata",
                qtip: OpenLayers.i18n("Tree.moreinfo")
            });
            nodeConfig.metadataUrl = item.metadataUrls[0].url;
        }
    },

    /**
     * Method: addScaleAction
     * Adds the "zoom to scale" action
     */
    addScaleAction: function(item, nodeConfig) {
        var maxResolutionHint = item.maxResolutionHint,
            minResolutionHint = item.minResolutionHint;
        if (maxResolutionHint || minResolutionHint) {
            nodeConfig.actions.push({
                action: "zoomtoscale",
                qtip: OpenLayers.i18n("Tree.zoomtoscale")
            });
        }
    },

    /**
     * Method: getOpacitySlider
     * Adds the opacity slider block
     *
     * Parameters:
     * theme {Object}
     */
    getOpacitySlider: function(theme) {
        var slider = new GeoExt.LayerOpacitySlider({
            layer: theme.layer,
            width: 265,
            isFormField: true,
            hideLabel: true,
            aggressive: true,
            plugins: new GeoExt.LayerOpacitySliderTip({
                template: '<div>' + OpenLayers.i18n('Tree.opacitylabel') + ' {opacity}%</div>'
            })
        });
        slider.on('changecomplete', function() {
            this.fireEvent('themeopacitychange');
        }, this);
        return new Ext.Container({
            layout: 'form',
            items: [slider],
            listeners: {
                render: function(cmp) {
                    cmp.getEl().setVisibilityMode(Ext.Element.DISPLAY);
                    cmp.getEl().hide.defer(1, cmp.getEl(), [false]);
                }
            }
        });
    },

    /**
     * Method: onAction
     * Called when a action image is clicked
     */
    onAction: function(node, action, evt) {
        var layer = node.layer,
            key;
        if (action.indexOf('legend') != -1) {
            action = 'legend';
        }
        switch (action) {
            case 'metadata':
                window.open(node.attributes.metadataUrl);
                break;
            case 'delete':
                var tree = node.getOwnerTree();
                node.remove();
                node.layer.destroy();
                tree.fireEvent('removegroup');
                break;
            case 'opacity':
                var slider = node.component;
                if (!slider.getEl().isVisible()) {
                    slider.el.setVisibilityMode(Ext.Element.DISPLAY);
                    slider.el.slideIn('t', {
                        useDisplay: true,
                        duration: 0.2,
                        callback: function(el) {
                            if (Ext.isIE) {
                                el.show({
                                    duration: 0.01
                                });
                            }
                        }
                    });
                } else {
                    slider.el.setVisibilityMode(Ext.Element.DISPLAY);
                    slider.el.slideOut('t', {
                        useDisplay: true,
                        duration: 0.2
                    });
                }
                break;
            case 'down':
                layer.map.raiseLayer(layer, -1);
                node.parentNode.insertBefore(node, node.nextSibling.nextSibling);
                node.ownerTree.actionsPlugin.updateActions(node);
                node.ui.removeClass('x-tree-node-over');
                if(Ext.enableFx){
                    node.ui.highlight(); 
                }
                node.getOwnerTree().fireEvent('ordergroup');
                break;
            case 'up':
                layer.map.raiseLayer(layer, +1);
                node.parentNode.insertBefore(node, node.previousSibling);
                node.ownerTree.actionsPlugin.updateActions(node);
                node.ui.removeClass('x-tree-node-over');
                if(Ext.enableFx){
                    node.ui.highlight(); 
                }
                node.getOwnerTree().fireEvent('ordergroup');
                break;
            case 'legend':
                key = 'legend';
                break;
            case 'zoomtoscale':
                    var n = node,
                    map = n.layer.map,
                    res = map.getResolution(),
                    zoom,
                    center = map.getCenter(),
                    minResolutionHint = n.attributes.minResolutionHint,
                    maxResolutionHint = n.attributes.maxResolutionHint;
                if (maxResolutionHint && maxResolutionHint < res) {
                    zoom = map.getZoomForResolution(maxResolutionHint) + 1;
                } else if (minResolutionHint && minResolutionHint > res) {
                    zoom = map.getZoomForResolution(minResolutionHint);
                }
                map.setCenter(center, zoom);
        }

        if (key) {
            var actionImg = evt.getTarget('.' + action, 10, true);
            var cls = action + "-on"; 
            if (!node[key].getEl().isVisible()) {
                actionImg.addClass(cls);
                node[key].el.setVisibilityMode(Ext.Element.DISPLAY);
                node[key].el.slideIn('t', {
                    useDisplay: true,
                    duration: 0.2,
                    callback: function(el) {
                        if (Ext.isIE) {
                            el.show({
                                duration: 0.01
                            });
                        }
                    }
                });
            } else {
                actionImg.removeClass(cls);
                node[key].el.setVisibilityMode(Ext.Element.DISPLAY);
                node[key].el.slideOut('t', {
                    useDisplay: true,
                    duration: 0.2
                });
            }
        }
    },

    /**
     * Method: checkVisibility
     * Checks layer visibility for the node (in case the node was previously hidden)
     */
    checkVisibility: function(node) {
        // if node is LayerParamNode, set the node check correctly
        if (node.attributes.nodeType == 'gx_layerparam') {
            //node.attributes.checked =
                //node.layer.getVisibility() &&
                //node.getItemsFromLayer().indexOf(node.item) >= 0;
        }
    },

    /**
     * Method: parseChildren
     * Parses recursively the children of a theme node.
     * 
     * Parameters:
     * child {Object} the node to parse
     * layer {<OpenLayers.Layer.WMS>} The reference to the OL Layer
     * allLayers {Array(String)} The list of WMS subLayers for this layer.
     */
    parseChildren: function(child, layer, allLayers) {
        if (child.children) {
            for (var j = 0; j < child.children.length; j++) {
                this.parseChildren(child.children[j], layer, allLayers);
            }
        } else {
            allLayers.push(child.name);
            // put a reference to ol layer in the config object
            child.layer = layer;
        }
    },

    /**
     * Method: loadTheme
     * Loads a theme from the config.
     *
     * Parameters:
     * theme {Object} the theme config
     * layers {Array} the sub layers displayed at once. optional.
     * opacity {Float} the OL layer opacity. optional
     * visibility {Boolean} the OL layer visibility. optional
     */
    loadTheme: function(theme) {
        Ext.each(theme.children, function(group) {
            this.loadGroup(group);
        }, this);
    },

    /**
     * Method: loadGroup
     * Loads a layer group from the config.
     *
     * Parameters:
     * group {Object} the group config
     * layers {Array} the sub layers displayed at once. optional.
     * opacity {Float} the OL layer opacity. optional
     * visibility {Boolean} the OL layer visibility. optional
     */
    loadGroup: function(group, layers, opacity, visibility) {
        var params = {
            layers: [],
            format: 'image/png',
            transparent: true
        };

        var isExternalgroup = function(name) {
            for (var i = 0, len = App.themes.external.length; i < len; i++) {
                for (var j = 0, len2 = App.themes.external[i].children.length; j<len2; j++) {
                    if (App.themes.external[i].children[j].name == name) {
                        return true;
                    }
                }
            }
            return false;
        };
        if (App.themes.external != undefined && isExternalgroup(group.name)) {
            params.external = true;
        }

        var layer = new OpenLayers.Layer.WMS(
            OpenLayers.i18n(group.name),
            this.wmsURL, params, {
                ref: group.name,
                singleTile: true,
                isBaseLayer: false
            }
        );

        var allLayers = [];
        this.parseChildren(group, layer, allLayers);
        group.layer = layer;
        group.allLayers = allLayers; 
        layer.params.LAYERS = layers || allLayers;
        this.map.addLayers([layer]);
        this.addGroup(group);
        layer.setOpacity(opacity || 1);
        layer.setVisibility(visibility !== 'false');
    },

    checkGroupIsAllowed: function(group) {
        var checkGroup = function(group, themes) {
            for (var i = 0, len = themes.length; i < len; i++) {
                for (var j = 0, len2 = themes[i].children.length; j < len2; j++) {
                    if (themes[i].children[j].name == group) {
                        return true;
                    }
                }
            }
            return false;
        };

        var isAllowed = checkGroup(group, App.themes.local);
        if (App.themes.external != undefined && !isAllowed) {
            isAllowed = checkGroup(group, App.themes.external);
        }
        return isAllowed;
    },

    applyState: function(state) {
        if (state.groups) {
            this.defaultThemes = null;
        }
        var groups = Ext.isArray(state.groups) ?
            state.groups : [state.groups];
        Ext.each(groups.reverse(), function(t) {
            if (!this.checkGroupIsAllowed(t)) {
                return;
            }
            var opacity = state['group_opacity_' + t];
            var visibility = state['group_visibility_' + t];
            var layers = state['group_layers_' + t];
            var group = this.findGroupByName(t);
            this.on('afterrender', function() {
                this.loadGroup(group, layers, opacity, visibility);
            }, this);
        }, this);
    },

    getState: function() {
        var state = {};

        var groups = [];
        Ext.each(this.root.childNodes, function(group) {
            var id = group.attributes.groupId;
            groups.push(id);
            var layer = group.layer;
            state['group_opacity_' + id] = (layer.opacity !== null) ?
                layer.opacity : 1;
            state['group_visibility_' + id] = layer.visibility;
            state['group_layers_' + id] = [layer.params.LAYERS].join(',');
        }, this);
        state.groups = groups.join(',');

        return state;
    },


    /**
     * Method: findGroupByName
     * Finds the group config using its name
     *
     * Parameters:
     * name {String}
     */
    findGroupByName: function(name) {
        var group = false;
        Ext.each(['local', 'external'], function(location) {
            Ext.each(this.themes[location], function(t) {
                Ext.each(t.children, function(g) {
                    if (g.name == name) {
                        group = g;
                        return false;
                    }
                }, this);
                if (group) {
                    return false;
                }
            }, this);
            if (group) {
                return false;
            }
        }, this);
        return group;
    },


    /**
     * Method: findThemeByName
     * Finds the theme config using its name
     *
     * Parameters:
     * name {String}
     */
    findThemeByName: function(name) {
        var theme = false;
        Ext.each(['local', 'external'], function(location) {
            Ext.each(this.themes[location], function(t) {
                if (t.name == name) {
                    theme = t;
                    return false;
                }
            }, this);
            if (theme) {
                return false;
            }
        }, this);
        return theme;
    },

    /**
     * Method: checkInRange
     * Checks if a layer is in range (correct scale) and modifies node
     * rendering consequently
     */
    checkInRange: function(node) {
        if (!node.layer) {
            return;
        }
        var n = node,
            map = n.layer.map,
            resolution = map.getResolution(),
            minResolutionHint = n.attributes.minResolutionHint,
            maxResolutionHint = n.attributes.maxResolutionHint;
        if (n.getUI().rendered) {
            var actions = Ext.select(".gx-tree-layer-actions img", true, n.getUI().elNode);
            actions.setVisibilityMode(Ext.Element.DISPLAY);
            var zoomToScale = Ext.select(".gx-tree-layer-actions img.zoomtoscale", true, n.getUI().elNode);

            if ((minResolutionHint && minResolutionHint > resolution) || (maxResolutionHint && maxResolutionHint < resolution)) {
                n.getUI().addClass("gx-tree-layer-outofrange");
                actions.hide();
                zoomToScale.show();
            } else if (minResolutionHint || maxResolutionHint) {
                n.getUI().removeClass("gx-tree-layer-outofrange");
                actions.show();
                zoomToScale.hide();
            }
        }
    }
});
App.LayerNode = Ext.extend(GeoExt.tree.LayerNode, {
    // we don't want the layer to manage the checkbox to avoid conflicts with the tristate manager
    onLayerVisibilityChanged: Ext.emptyFn
});
Ext.tree.TreePanel.nodeTypes.app_layer = App.LayerNode; 
