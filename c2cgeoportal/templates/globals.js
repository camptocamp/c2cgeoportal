<%!
    import urlparse
%>
// this code may execute before the App namespace exists. If it
// does not exist, we create it ourselves.
if(!window.App) App = {};
App["OpenLayers.ImgPath"] = "${request.static_url('project:static/lib/cgxp/core/src/theme/img/ol/')}";
App["Ext.BLANK_IMAGE_URL"] = "${request.static_url('project:static/lib/cgxp/ext/Ext/resources/images/default/s.gif')}";
App["fullTextSearchURL"] = "${request.route_url('fulltextsearch', path='')}";
% if len(tilecache_url) == 0:
App["tilecacheURL"] = "${request.route_url('tilecache', path='')}";
% else:
App["tilecacheURL"] = '${tilecache_url}';
% endif
App["mapserverproxyURL"] = "${request.route_url('mapserverproxy', path='')}";
App["printURL"] = "${request.route_url('printproxy', path='')}";
App["csvURL"] = "${request.route_url('csvecho')}";
App["loginURL"] = "${request.route_url('login')}";
App["logoutURL"] = "${request.route_url('logout')}";
App["overwiewImageType"] = "${overwiewimage_type}";
App["overwiewImage"] = "${request.static_url(overwiewimage)}";
App["overwiewImageBounds"] = ${overwiewimage_bounds};
App["overwiewImageSize"] = ${overwiewimage_size};
App["lang"] = "${lang}";
% if user:
App["user"] = "${user.username}";
App["extent"] = ${user.role.jsextent};
% else:
App["extent"] = ${default_initial_extent | n};
% endif
App["restrictedExtent"] = ${restricted_extent | n};
/*${themesError | n}*/
App["themes"] = {
    "local": ${themes | n}
% if external_themes:
    , "external": ${external_themes | n}
% endif
};
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
