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

/**
 * This list auto heights itself by using its items height.
 */
Ext.define("App.view.AutoHeightList", {
    extend: 'Ext.dataview.List',
    xtype: 'autoheightlist',

    setStore: function() {
        this.callParent(arguments);
        this.getStore().on({
            'load': this.resize,
            'addrecords': this.resize,
            scope: this
        });
    },

    resize: function() {
        Ext.defer(function() {
            var totalHeight = 0;
            Ext.each(this.getViewItems(), function(item) {
                totalHeight += item.element.getHeight();
            });
            var padding = 40;
            this.setHeight(totalHeight + padding);
        }, 500, this);
    }
});
