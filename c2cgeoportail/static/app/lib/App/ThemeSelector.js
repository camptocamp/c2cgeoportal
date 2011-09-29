Ext.namespace('App');

App.ThemeSelector = function(themes, tree) {

   var tpl = new Ext.XTemplate(
        '<tpl for=".">',
            '<div class="thumb-wrap">',
            '<div class="thumb"><img src="{icon}"></div>',
            '<span>{name}</span></div>',
        '</tpl>',
        '<div class="x-clear"></div>'
    );

    var config = {
        fields: ['name', 'icon', 'children']
    };
    var localStore = new Ext.data.JsonStore(Ext.apply(config, {
        data: themes.local
    }));
    var externalStore = new Ext.data.JsonStore(Ext.apply(config, {
        data: themes.external || [] 
    }));

    config =  {
        tpl: tpl,
        overClass: 'x-view-over',
        itemSelector:'div.thumb-wrap',
        singleSelect: true,
        width: 560,
        cls: 'theme-selector',
        listeners: {
            selectionchange: function(view, nodes) {
                var record = view.getRecords(nodes)[0];
                if (record) {
                    tree.loadTheme.apply(tree, [record.data]);
                }
                button.menu.hide();
            }
        }
    };
    var localView = new Ext.DataView(Ext.apply({
        title: OpenLayers.i18n('Themeselector.local'),
        store: localStore
    }, config));
    var externalView = new Ext.DataView(Ext.apply({
        title: OpenLayers.i18n('Themeselector.external'),
        store: externalStore
    }, config));

    var items = [localView];
    if (themes.external) {
        items.push(externalView);
    }
    var tabs = new Ext.TabPanel({
        width: 560,
        activeItem: 0,
        plain: true,
        border: false,
        tabPosition: 'bottom',
        items: items 
    });

    var button = new Ext.Button({
        text: OpenLayers.i18n("Themeselector.themes"),
        cls: "themes",
        iconCls: 'themes',
        scale: 'large',
        width: '100%',
        menu: [{
            xtype: 'container',
            layout: 'fit',
            items: [tabs]
        }]
    });
    this.button = button;
};
