% if debug:
<%block name="page_urls_debug">\
document.write('
## include debug js files
');
document.write('
## include debug css files
');
</%block>\
% else:
<%block name="page_urls_nodebug">\
document.write('<scr' + 'ipt type="text/javascript" src="' + "${request.static_url('c2cgeoportal:static/build/api.js')}" + '"></scr' + 'ipt>');
% if lang != 'en':
document.write('<scr' + 'ipt type="text/javascript" src="' + "${request.static_url('c2cgeoportal:static/build/lang-%s.js' % lang)}" + '"></scr' + 'ipt>');
% endif
document.write('<link rel="stylesheet" type="text/css" href="' + "${request.static_url('c2cgeoportal:static/build/app.css')}" + '" />');
</%block>\
% endif

API = {};
API.getViewer = function(config) {
    <%include file="apiviewer.js" />
    return app;
}

