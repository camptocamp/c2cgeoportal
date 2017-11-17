import os
from c2cgeoform.routes import register_models


def includeme(config):
    config.add_static_view('node_modules', 'c2cgeoportal_admin:node_modules/')
    config.override_asset(to_override='c2cgeoportal_admin:node_modules/',
                          override_with=os.path.join(os.path.dirname(__file__),
                                                     '..',
                                                     'node_modules'))

    config.add_static_view('static', 'static', cache_max_age=3600)

    config.add_route('home', '/')
    config.add_route('layertree', '/layertree/')
    config.add_route('layertree_unlink', '/layertree/unlink/{group_id}/{item_id}')
    config.add_route('layertree_delete', '/layertree/delete/{item_id}')

    from c2cgeoportal_commons.models.main import Role
    from c2cgeoportal_commons.models.static import User
    from c2cgeoportal_commons.models.main import LayerWMS
    register_models(config, (
        ('roles', Role),
        ('users', User),
        ('layers_wms', LayerWMS),
    ))
