import os
from c2cgeoform.routes import register_models, table_pregenerator


def includeme(config):
    config.add_static_view('node_modules', 'c2cgeoportal_admin:node_modules/')
    path = os.path.join(os.path.dirname(__file__), '..', 'node_modules')
    if not os.path.exists(path):
        path = '/usr/lib/node_modules/'

    config.override_asset(
        to_override='c2cgeoportal_admin:node_modules/',
        override_with=path
    )

    config.add_static_view('static', 'static', cache_max_age=3600)

    config.add_route('home', '/')
    config.add_route('layertree', '/layertree')
    config.add_route('layertree_nodes', '/layertree/nodes')
    config.add_route('layertree_ordering', '/layertree/ordering')
    config.add_route('layertree_unlink', '/layertree/unlink/{group_id}/{item_id}')
    config.add_route('layertree_delete', '/layertree/delete/{item_id}')
    config.add_route('convert_to_wms',
                     '/{table:layers_wmts}/{id}/convert_to_wms',
                     pregenerator=table_pregenerator)
    config.add_route('convert_to_wmts',
                     '/{table:layers_wms}/{id}/convert_to_wmts',
                     pregenerator=table_pregenerator)

    from c2cgeoportal_commons.models.main import (
        Role, LayerWMS, LayerWMTS, Theme, LayerGroup, LayerV1, Interface, OGCServer,
        Functionality, RestrictionArea)
    from c2cgeoportal_commons.models.static import User

    register_models(config, (
        ('themes', Theme),
        ('layer_groups', LayerGroup),
        ('layers_wms', LayerWMS),
        ('layers_wmts', LayerWMTS),
        ('layers_v1', LayerV1),
        ('ogc_servers', OGCServer),
        ('restriction areas', RestrictionArea),
        ('users', User),
        ('roles', Role),
        ('functionalities', Functionality),
        ('interfaces', Interface),
    ))
