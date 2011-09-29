Ext.namespace("App");
App.TreeNodeLoading = Ext.extend(Ext.util.Observable, {
    
    /** private: method[constructor]
     *  :param config: ``Object``
     */
    constructor: function(config) {
        Ext.apply(this.initialConfig, Ext.apply({}, config));
        Ext.apply(this, config);

        App.TreeNodeLoading.superclass.constructor.apply(this, arguments);
    },

    /** private: method[init]
     *  :param tree: ``Ext.tree.TreePanel`` The tree.
     */
    init: function(tree) {
        tree.root.on({
            "append": this.onAppendNode,
            "insert": this.onAppendNode,
            scope: this
        });
        tree.on({
            "beforedestroy": this.onBeforeDestroy,
            scope: this
        });
    },
    
    /** private: method[onAppendNode]
     *  :param node: ``Ext.tree.TreeNode``
     */
    onAppendNode: function(tree, parentNode, node) {
        var rendered = node.rendered;
        if(!rendered && node.layer) {
            var layer = node.layer;
            layer.events.on({
                'loadstart': function() {
                    if (node.ui.isChecked()) {
                        Ext.get(node.ui.elNode).addClass('gx-tree-node-loading');
                    }
                },
                'loadend': function() {
                    Ext.get(node.ui.elNode).removeClass('gx-tree-node-loading');
                }
            });
        }
    },
    
    /** private: method[onBeforeDestroy]
     */
    onBeforeDestroy: function(tree) {
        tree.un("beforedestroy", this.onBeforeDestroy, this);
    }
});

