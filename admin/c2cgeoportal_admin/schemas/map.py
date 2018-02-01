import colander
from c2cgeoform.ext.deform_ext import MapWidget


@colander.deferred
def map_widget(node, kw):  # pylint: disable=unused-argument
    settings = kw['request'].registry.settings['admin_interface']
    return MapWidget(
        base_layer=settings.get('map_base_layer', MapWidget.base_layer),
        center=[
            settings.get('map_x', MapWidget.center[0]),
            settings.get('map_y', MapWidget.center[1])],
        zoom=settings.get('map_zoom', MapWidget.zoom),
        fit_max_zoom=settings.get('map_fit_max_zoom', MapWidget.fit_max_zoom)
    )
