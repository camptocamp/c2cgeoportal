import os
from c2cgeoform.routes import register_models, table_pregenerator


def includeme(config):
    config.add_static_view('node_modules_for_insider', 'c2cgeoportal_admin:node_modules')
    config.add_static_view(
        'node_modules_for_outsider',
        '{}:node_modules'.format(config.root_package.__name__))
    path = None
    for path_ in [
        os.path.join(os.path.dirname(__file__), '..', '..', 'admin', 'node_modules'),
        os.path.join(os.path.dirname(__file__), '..', '..', 'node_modules'),
        os.path.join(os.path.dirname(__file__), '..', 'admin', 'node_modules'),
        os.path.join(os.path.dirname(__file__), '..', 'node_modules'),
        '/usr/lib/node_modules/',
    ]:
        if os.path.exists(path_):
            path = path_
            break
    if path is None:
        raise Exception("Unable to find the node_module from path '{}'.".format(os.path.dirname(__file__)))

    config.override_asset(
        to_override='c2cgeoportal_admin:node_modules/',
        override_with=path
    )
    config.override_asset(
        to_override='{}:node_modules/'.format(config.root_package.__name__),
        override_with=path
    )

    config.add_static_view('static', 'c2cgeoportal_admin:static', cache_max_age=3600)

    config.add_route('home', '/')
    config.add_route('layertree', '/layertree')
    config.add_route('layertree_children', '/layertree/children')
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
        ('restriction_areas', RestrictionArea),
        ('users', User),
        ('roles', Role),
        ('functionalities', Functionality),
        ('interfaces', Interface),
    ))
