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

Ext.define("App.view.Query", {
    extend: 'Ext.Container',
    xtype: 'queryview',
    requires: ['Ext.dataview.List', 'App.model.Query', 'App.view.AutoHeightList'],

    config: {
        scrollable: {
            direction: 'vertical'
        },
        items: [{
            docked: 'top',
            xtype: 'toolbar',
            items: [{
                xtype: 'spacer'
            }, {
                xtype: 'button',
                text: OpenLayers.i18n('close'),
                action: 'home'
            }]
        }, {
            pseudo: 'coordinates'
        }, {
            xtype: 'autoheightlist',
            itemTpl: '<div>{detail}</div>',
            selectedCls: '',
            emptyText: OpenLayers.i18n('No query result'),
            store: 'queryStore',
            onItemDisclosure: true,
            pinHeaders: true,
            ui: 'round',
            grouped: true,
            height: 0,
            scrollable: false
        }]
    }
});
