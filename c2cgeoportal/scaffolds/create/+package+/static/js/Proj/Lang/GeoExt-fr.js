/*
 * @requires GeoExt/Lang.js
 */

GeoExt.Lang.add("en", {
    "cgxp.plugins.ContextualData.Tooltip.prototype": {
        defaultTpl: "Coordonnées suisses : {coord_x} {coord_y}<br />" +
            "WGS 84 : {wsg_x} {wsg_y}<br />",
    },

    "cgxp.plugins.ContextualData.ContextPopup.prototype": {
        coordTpl: "<tr><td width=\"150\">Coordonnées suisses</td>" +
            "<td>{coord_x} {coord_y}</td></tr>" +
            "<tr><td>WGS 84</td><td>{wsg_x} {wsg_y}</td></tr>",
    }
});
