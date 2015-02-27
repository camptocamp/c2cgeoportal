<%
# default configuration options that will be used when
# no field options were set, e.g. with:
#
# Place = FieldSet(model.places.Place)
# Place.the_geom.set(options=[('zoom', 12), ..])

options = {}
options['zoom'] = 4
options['map_width'] = 700
options['map_height'] = 400
from pyramid.threadlocal import get_current_request
options['image_select_feature_on'] = get_current_request().static_url('c2cgeoportal:static/adminapp/images/select_feature_on.png')
options['image_select_feature_off'] = get_current_request().static_url('c2cgeoportal:static/adminapp/images/select_feature_off.png')
options['image_remove_feature_on'] = get_current_request().static_url('c2cgeoportal:static/adminapp/images/remove_feature_on.png')
options['image_remove_feature_off'] = get_current_request().static_url('c2cgeoportal:static/adminapp/images/remove_feature_off.png')
%>

% if insert_libs:
<style>
.formmap {
    border: 1px solid #ccc;
    ## temporarily fix issue addressed in openlayers ticket #1635 :
    ## http://trac.osgeo.org/openlayers/ticket/1635#comment:7
    ## (to be remove when this ticket is closed)
    position: relative;
    z-index: 0;
}

.olControlAttribution {
    bottom: 2px;
    right: 10px;
}

.olControlEditingToolbar .olControlModifyFeatureItemActive {
    background-image: url("${image_select_feature_on or options['image_select_feature_on']}");
}
.olControlEditingToolbar .olControlModifyFeatureItemInactive {
    background-image: url("${image_select_feature_off or options['image_select_feature_off']}");
}

.olControlEditingToolbar .olControlDeleteFeatureItemActive {
    background-image: url("${image_remove_feature_on or options['image_remove_feature_on']}");
}
.olControlEditingToolbar .olControlDeleteFeatureItemInactive {
    background-image: url("${image_remove_feature_off or options['image_remove_feature_off']}");
}

</style>

<script type="text/javascript">
    <%include file="map_js.mako" />
</script>
% endif

<div>
    ${input_field}
    <div id="map_${field_name}" class="formmap"
       style="width: ${map_width or options['map_width']}px; height: ${map_height or options['map_height']}px;"></div>
    % if run_js:
    <script>
    ${_renderer.render_runjs(read_only)}
    </script>
    % endif
    <br />
</div>
