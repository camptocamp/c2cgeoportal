<%inherit file="viewer.js"/>

<%block name="viewer_portal_config">\
items: [config.renderTo],
width: config.width,
height: config.height,
renderTo: config.renderTo
</%block>\

<%block name="viewer_tools_themeselector">\
</%block>\

<%block name="viewer_tools_layertree">\
</%block>\

<%block name="viewer_tools_querier">\
</%block>\

<%block name="viewer_tools_print">\
</%block>\

<%block name="viewer_tools_featuregrid">\
</%block>\

<%block name="viewer_tools_toolbar_permalink">\
</%block>\

<%block name="viewer_tools_toolbar_getfeatureinfo">\
</%block>\

<%block name="viewer_tools_toolbar_login">\
</%block>\

<%block name="viewer_map_id">\
    id: config.renderTo, // id needed to reference map in portalConfig above
</%block>\

<%block name="viewer_add_controls">\
</%block>\

<%block name="viewer_ready">\
</%block>\
