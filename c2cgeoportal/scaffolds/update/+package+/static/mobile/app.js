/**
 * Copyright (c) 2011-2014 by Camptocamp SA
 *
 * CGXP is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * CGXP is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with CGXP. If not, see <http://www.gnu.org/licenses/>.
 */

Ext.application({
    name: 'App',
    appFolder: 'app',

    viewport: {
        // hide the address bar
        // autoMaximize set to false. See "AutoMaximize No More!" in
        // http://www.sencha.com/blog/top-sencha-support-tips/
        //autoMaximize: true
    },

    requires: [
        'Ext.viewport.Viewport',
        'Ext.MessageBox',
        'Ext.data.Store',
        'Ext.data.proxy.JsonP',
        'Ext.TitleBar', // required at least for the Picker
        'Ext.JSON',
        'Ext.ActionSheet',
        'Ext.TitleBar' // required at least for the Picker
    ],

    views: ['Main', 'Layers', 'Themes', 'Search', 'Query', 'Settings', 'LoginForm'],
    models: ['Layer', 'Search', 'Query', 'Theme'],
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
        this.getController('Main').loadTheme(App.theme);

        // create the main view and set the map into it
        var mainView = Ext.create('App.view.Main');

        // App.map should be set in config.js
        mainView.setMap(App.map);

        var layersView = Ext.create('App.view.Layers');

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
        if (Ext.os.is.Tablet || Ext.os.is.Desktop) {
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
