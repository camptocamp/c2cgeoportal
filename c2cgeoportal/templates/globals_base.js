<%!
    import urlparse
%>
// this code may execute before the App namespace exists. If it
// does not exist, we create it ourselves.
if(!window.App) App = {};
% if len(tilecache_url) == 0:
App["tilecacheURL"] = "${request.route_url('tilecache', path='')}";
% else:
App["tilecacheURL"] = '${tilecache_url}';
% endif
App["mapserverproxyURL"] = "${request.route_url('mapserverproxy', path='')}";
App["printURL"] = "${request.route_url('printproxy', path='')}";
App["csvURL"] = "${request.route_url('csvecho')}";
App["lang"] = "${lang}";
App["restrictedExtent"] = ${restricted_extent | n};
/*${themesError | n}*/
App["themes"] = {
    "local": ${themes | n}
% if external_themes:
    , "external": ${external_themes | n}
% endif
};
App["default_themes"] = ${default_themes | n};
App["HelpURL"] = "${request.static_url('c2cgeoportal:static/app/pdf/Hilfedokument_geoag.pdf')}";
App["queryBuilderLayer"] = "${query_builder_layer}";
% if encodedLayers_plan and encodedLayers_plan_color and encodedLayers_ortho:
App["encodedLayers"] = {
    "plan": ${encodedLayers_plan | n},
    "plan_color": ${encodedLayers_plan_color | n},
    "ortho": ${encodedLayers_ortho | n}
};
App["functionality"] = ${functionality | n};
App["functionalities"] = ${functionalities | n};
% endif
<%block name="globals">\
</%block>\
