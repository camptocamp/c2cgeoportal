Ext.application({
    name: 'App',
    appFolder: 'app',

    viewport: {
        // hide the address bar
        autoMaximize: true
    },

    requires: [
        'Ext.MessageBox',
        'Ext.data.Store',
        'Ext.data.proxy.JsonP',
        'Ext.TitleBar', // required at least for the Picker
        'Ext.JSON',
        'Ext.ActionSheet',
        'Ext.TitleBar' // required at least for the Picker
    ],

    views: ['Main', 'Layers', 'Search', 'Query', 'Settings', 'LoginForm'],
    models: ['Layer', 'Search', 'Query'],
    controllers: ['Main', 'Search', 'Query'],

    icon: {
        '57': 'resources/icons/Icon.png',
        '72': 'resources/icons/Icon~ipad.png',
        '114': 'resources/icons/Icon@2x.png',
        '144': 'resources/icons/Icon~ipad@2x.png'
    },

    isIconPrecomposed: true,

    startupImage: {
        '320x460': 'resources/startup/320x460.jpg',
        '640x920': 'resources/startup/640x920.png',
        '768x1004': 'resources/startup/768x1004.png',
        '748x1024': 'resources/startup/748x1024.png',
        '1536x2008': 'resources/startup/1536x2008.png',
        '1496x2048': 'resources/startup/1496x2048.png'
    },

    launch: function() {

        // decode the information received from the server
        if (App.info) {
            App.info = Ext.JSON.decode(App.info, true);
        }

        // create the main view and set the map into it
        var mainView = Ext.create('App.view.Main');
        // App.map should be set in config.js
        mainView.setMap(App.map);

        // destroy the #appLoadingIndicator element
        Ext.fly('appLoadingIndicator').destroy();

        // now add the main view to the viewport
        Ext.Viewport.add(mainView);

        this.handleTablet();
    },

    onUpdated: function() {
        window.location.reload();
    },

    handleTablet: function() {
        if (Ext.os.is.Tablet) {
            var msg = OpenLayers.String.format(
                OpenLayers.i18n('redirect_msg'),
                {
                    url: App.desktopAppUrl
                }
            );
            msg += "<a href='#' class='close' style='float:right'>" +
                   OpenLayers.i18n('close') + "</a>";
            var actionSheet = Ext.create('Ext.ActionSheet', {
                ui: 'redirect',
                modal: false,
                html: msg
            });

            Ext.Viewport.add(actionSheet);
            actionSheet.show();
            Ext.Function.defer(function() {
                actionSheet.hide();
            }, 15000);
            actionSheet.element.on({
                'tap': function(e) {
                    if (Ext.get(e.target).hasCls('close')) {
                        actionSheet.hide();
                    }
                }
            });
        }
    }
});
