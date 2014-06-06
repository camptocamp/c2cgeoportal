/**
 * Copyright (c) 2011-2013 by Camptocamp SA
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

Ext.define('App.view.LoginForm', {
    extend: 'Ext.form.Panel',
    xtype: 'loginformview',
    requires: [
        'Ext.form.FieldSet',
        'Ext.field.Text',
        'Ext.field.Password',
        'Ext.Container',
        'Ext.Button'
    ],
    fullscreen: true,
    config: {
        url: App.loginUrl,
        method: 'POST',
        standardSubmit: false,
        listeners: {
            exception: function (self, result, eOpts) {
                if (result === true) {
                    var sep = App.cameFrom.indexOf('?') > 0 ? '&' : '?';
                    window.location = App.cameFrom + sep + 'v=' + Math.round(Math.random() * 1000000);
                }
                else {
                    if (result.status == 401) {
                        Ext.Msg.alert(OpenLayers.i18n('unauthorized'), OpenLayers.i18n('wrongUserPass'));
                    }
                    else {
                        Ext.Msg.alert(OpenLayers.i18n('unauthorized'), result.statusText);
                    }
                }
            }
        },
        items: [{
            xtype: 'fieldset',
            defaults: {
                // labelWidth default is 35% and is too
                // small on small devices (e.g.g iPhone)
                labelWidth: 130
            },
            items: [{
                xtype: 'textfield',
                name: 'login',
                label: OpenLayers.i18n('loginLabel')
            }, {
                xtype: 'passwordfield',
                name: 'password',
                label: OpenLayers.i18n('passwordLabel')
            }]
        }, {
            xtype: 'container',
            layout: {
                type: 'hbox',
                align: 'start',
                pack: 'center'
            },
            items: [{
                xtype: 'button',
                text: OpenLayers.i18n('loginCancelButtonText'),
                action: 'home',
                margin: 2
            }, {
                xtype: 'button',
                text: OpenLayers.i18n('loginSubmitButtonText'),
                ui: 'confirm',
                action: 'login',
                margin: 2
            }]
        }]
    }
});
