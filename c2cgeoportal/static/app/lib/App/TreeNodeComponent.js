/**
 * @include GeoExt/plugins/TreeNodeComponent.js
 */
Ext.namespace("App");
App.TreeNodeComponent = Ext.extend(GeoExt.plugins.TreeNodeComponent, {


    divCls: null,

    configKey: 'component',
    
    /** private: method[onRenderNode]
     *  :param node: ``Ext.tree.TreeNode``
     */
    onRenderNode: function(node) {
        var rendered = node.rendered;
        var attr = node.attributes;
        var component = attr[this.configKey] || this[this.configKey];
        if(!rendered && component) {
            var elt = Ext.DomHelper.append(node.ui.elNode, [
                {"tag": "div", "class": this.divCls}
            ]);
            if(typeof component == "function") {
                component = component(node, elt);
            } else if (typeof component == "object" &&
                       typeof component.fn == "function") {
                component = component.fn.apply(
                    component.scope, [node, elt]
                );
            }
            if(typeof component == "object" &&
               typeof component.xtype == "string") {
                component = Ext.ComponentMgr.create(component);
            }
            if(component instanceof Ext.Component) {
                component.render(elt);
                node[this.configKey] = component;
            }
        }
    }
});
