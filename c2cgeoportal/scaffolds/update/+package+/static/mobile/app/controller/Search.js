Ext.define('App.controller.Search', {
    extend: 'Ext.app.Controller',
    
    config: {
        refs: {
            searchField: 'searchfield[action=search]',
            searchView: {
                selector: 'searchview',
                xtype: 'searchview',
                autoCreate: true
            }
        },
        control: {
            searchField: {
                focus: function(field) {
                    // hide all items but search field so that it gets bigger
                    var toolbar = field.parent;
                    toolbar.items.each(function(item) {item.hide();});
                    field.show();
                },
                blur: function(field) {
                    var toolbar = field.parent;
                    toolbar.items.each(function(item) {item.show();});
                },
                action: function(field) {
                    this.redirectTo('search/' + encodeURIComponent(field.getValue()));
                    field.blur();
                }
            },
            searchView: {
                select: function(list, record) {
                    var f = new OpenLayers.Format.GeoJSON().read(record.raw)[0];
                    this.getApplication().getController('Main').recenterMap(f);
                },
                disclose: function(list, record) {
                    var f = new OpenLayers.Format.GeoJSON().read(record.raw)[0];
                    this.getApplication().getController('Main').recenterMap(f);
                }
            }
        },
        routes: {
            'search/:terms': 'showSearchResultView'
        }
    },
    
    //called when the Application is launched, remove if not needed
    launch: function(app) {
        
    },

    showSearchResultView: function(terms) {
        terms = decodeURIComponent(terms);
        var view = this.getSearchView();
        Ext.Viewport.setActiveItem(view);
        var store = view.getStore();
        store.getProxy().setExtraParams({
            'query': terms,
            'maxRows': 20
        });
        store.load();
    }
});
