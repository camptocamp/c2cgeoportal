% if debug:
document.write('<scr' + 'ipt type="text/javascript" src="' + "${request.static_url('c2cgeoportal:static/lib/ext/Ext/adapter/ext/ext-base.js')}" + '"></scr' + 'ipt>');
document.write('<scr' + 'ipt type="text/javascript" src="' + "${request.static_url('c2cgeoportal:static/lib/ext/Ext/ext-all-debug.js')}" + '"></scr' + 'ipt>');
document.write('<scr' + 'ipt type="text/javascript" src="' + "${request.static_url('c2cgeoportal:static/lib/ext/Ext/src/locale/ext-lang-%s.js' % lang)}" + '"></scr' + 'ipt>');

document.write('<scr' + 'ipt type="text/javascript" src="' + "${request.static_url('c2cgeoportal:static/lib/openlayers/lib/OpenLayers.js')}" + '"></scr' + 'ipt>');
document.write('<scr' + 'ipt type="text/javascript" src="' + "${request.static_url('c2cgeoportal:static/lib/openlayers/lib/OpenLayers/Lang/%s.js' % lang)}" + '"></scr' + 'ipt>');
document.write('<scr' + 'ipt type="text/javascript" src="' + "${request.static_url('c2cgeoportal:static/lib/geoext/lib/GeoExt.js')}" + '"></scr' + 'ipt>');

document.write('<scr' + 'ipt type="text/javascript" src="' + "${request.static_url('c2cgeoportal:static/lib/geoext.ux/ux/Measure/lib/GeoExt.ux/Measure.js')}" + '"></scr' + 'ipt>');
document.write('<scr' + 'ipt type="text/javascript" src="' + "${request.static_url('c2cgeoportal:static/lib/geoext.ux/ux/Measure/lib/GeoExt.ux/MeasureLength.js')}" + '"></scr' + 'ipt>');
document.write('<scr' + 'ipt type="text/javascript" src="' + "${request.static_url('c2cgeoportal:static/lib/geoext.ux/ux/Measure/lib/GeoExt.ux/MeasureArea.js')}" + '"></scr' + 'ipt>');

document.write('<scr' + 'ipt type="text/javascript" src="' + "${request.static_url('c2cgeoportal:static/lib/sandbox/Styler/ux/LayerStyleManager.js')}" + '"></scr' + 'ipt>');
document.write('<scr' + 'ipt type="text/javascript" src="' + "${request.static_url('c2cgeoportal:static/lib/sandbox/Styler/ux/widgets/StyleSelectorComboBox.js')}" + '"></scr' + 'ipt>');
document.write('<scr' + 'ipt type="text/javascript" src="' + "${request.static_url('c2cgeoportal:static/lib/sandbox/FeatureEditing/ux/FeatureEditing.js')}" + '"></scr' + 'ipt>');

document.write('<scr' + 'ipt type="text/javascript" src="' + "${request.static_url('c2cgeoportal:static/app/lib/App/FeaturePanel.js')}" + '"></scr' + 'ipt>');
document.write('<scr' + 'ipt type="text/javascript" src="' + "${request.static_url('c2cgeoportal:static/app/lib/App/globals.js')}" + '"></scr' + 'ipt>');
document.write('<scr' + 'ipt type="text/javascript" src="' + "${request.static_url('c2cgeoportal:static/app/lib/App/Lang/%s.js' % lang)}" + '"></scr' + 'ipt>');
document.write('<scr' + 'ipt type="text/javascript" src="' + "${request.static_url('c2cgeoportal:static/app/lib/App/Map.js')}" + '"></scr' + 'ipt>');
document.write('<scr' + 'ipt type="text/javascript" src="' + "${request.static_url('c2cgeoportal:static/app/lib/App/ToolButton.js')}" + '"></scr' + 'ipt>');
document.write('<scr' + 'ipt type="text/javascript" src="' + "${request.static_url('c2cgeoportal:static/app/lib/App/ToolWindow.js')}" + '"></scr' + 'ipt>');
document.write('<scr' + 'ipt type="text/javascript" src="' + "${request.static_url('c2cgeoportal:static/app/lib/App/Tools.js')}" + '"></scr' + 'ipt>');
document.write('<scr' + 'ipt type="text/javascript" src="' + "${request.static_url('c2cgeoportal:static/app/lib/App/Locator.js')}" + '"></scr' + 'ipt>');
document.write('<scr' + 'ipt type="text/javascript" src="' + "${request.static_url('c2cgeoportal:static/app/lib/App/TwinTriggerComboBox.js')}" + '"></scr' + 'ipt>');
document.write('<scr' + 'ipt type="text/javascript" src="' + "${request.static_url('c2cgeoportal:static/app/lib/App/Search.js')}" + '"></scr' + 'ipt>');
document.write('<scr' + 'ipt type="text/javascript" src="' + "${request.static_url('c2cgeoportal:static/lib/ext/Ext/src/ext-core/examples/jsonp/jsonp.js')}" + '"></scr' + 'ipt>');
document.write('<scr' + 'ipt type="text/javascript" src="' + "${request.static_url('c2cgeoportal:static/app/lib/App/API.js')}" + '"></scr' + 'ipt>');

document.write('<link rel="stylesheet" type="text/css" href="' + "${request.static_url('c2cgeoportal:static/lib/ext/Ext/resources/css/ext-all.css')}" + '" />');
document.write('<link rel="stylesheet" type="text/css" href="' + "${request.static_url('c2cgeoportal:static/lib/ext/Ext/resources/css/xtheme-gray.css')}" + '" />');
document.write('<link rel="stylesheet" type="text/css" href="' + "${request.static_url('c2cgeoportal:static/lib/openlayers/theme/default/style.css')}" + '" />');
document.write('<link rel="stylesheet" type="text/css" href="' + "${request.static_url('c2cgeoportal:static/lib/geoext.ux/ux/Measure/resources/css/measure.css')}" + '" />');
document.write('<link rel="stylesheet" type="text/css" href="' + "${request.static_url('c2cgeoportal:static/lib/sandbox/FeatureEditing/resources/css/feature-editing.css')}" + '" />');
document.write('<link rel="stylesheet" type="text/css" href="' + "${request.static_url('c2cgeoportal:static/app/css/main.css')}" + '" />');


% else:

document.write('<scr' + 'ipt type="text/javascript" src="' + "${request.static_url('c2cgeoportal:static/build/api.js')}" + '"></scr' + 'ipt>');
% if lang != 'en':
document.write('<scr' + 'ipt type="text/javascript" src="' + "${request.static_url('c2cgeoportal:static/build/lang-%s.js' % lang)}" + '"></scr' + 'ipt>');
% endif
document.write('<link rel="stylesheet" type="text/css" href="' + "${request.static_url('c2cgeoportal:static/build/app.css')}" + '" />');

% endif

<%include file="globals.js" />
