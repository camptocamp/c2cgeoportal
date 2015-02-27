<%
# default configuration options that will be used when
# no field options were set, e.g. with:
#
# Place = FieldSet(model.places.Place)
# Place.the_geom.set(options=[('zoom', 12), ..])

options = {}
options['default_lon'] = 10
options['default_lat'] = 45
options['zoom'] = 4
options['base_layer'] = 'new OpenLayers.Layer.WMS("WMS", "http://labs.metacarta.com/wms/vmap0", {layers: "basic"})'

%>
geoformalchemy.init_map(
    '${field_name}',
    ${read_only},
    ${is_collection},
    '${geometry_type}',
    ${default_lon or options['default_lon']},
    ${default_lat or options['default_lat']},
    ${zoom or options['zoom']},
    ${base_layer or options['base_layer'] | n},
    '${wkt}'
);
