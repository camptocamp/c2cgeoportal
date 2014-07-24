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

Ext.define('App.view.Login', {
    extend: 'Ext.Container',
    xtype: 'login',
    config: {
        layout: {
            type: 'vbox',
            align: 'left'
        }
    },
    initialize: function() {
        if (App.info) {
            var items;
            if (!App.info.username) {
                items = [{
                    xtype: 'button',
                    text: OpenLayers.i18n('loginButtonText'),
                    iconCls: 'lock',
                    action: 'loginform'
                }];
            } else {
                items = [{
                    xtype: 'component',
                    tpl: OpenLayers.i18n('welcomeText'),
                    data: {username: App.info.username}
                }, {
                    xtype: 'button',
                    text: OpenLayers.i18n('logoutButtonText'),
                    iconCls: 'unlock',
                    action: 'logout'
                }];
            }
            this.setItems(items);
        }
    }
});
