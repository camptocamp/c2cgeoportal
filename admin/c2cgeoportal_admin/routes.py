from c2cgeoform.routes import register_models, table_pregenerator


def includeme(config):
    config.add_static_view("c2cgeoportal_admin_node_modules", "c2cgeoportal_admin:node_modules")
    config.override_asset(
        to_override="c2cgeoportal_admin:node_modules/", override_with="/opt/c2cgeoportal/admin/node_modules"
    )
    # Because c2cgeoform widgets target {root_package}:node_modules/...
    asset_spec = "{}:node_modules/".format(config.root_package.__name__)
    config.add_static_view("root_package_node_modules", asset_spec)
    config.override_asset(to_override=asset_spec, override_with="/opt/c2cgeoportal/admin/node_modules")

    config.add_static_view("static", "c2cgeoportal_admin:static", cache_max_age=3600)

    config.add_route("home", "/")
    config.add_route("layertree", "/layertree")
    config.add_route("layertree_children", "/layertree/children")
    config.add_route("layertree_ordering", "/layertree/ordering")
    config.add_route("layertree_unlink", "/layertree/unlink/{group_id}/{item_id}")
    config.add_route("layertree_delete", "/layertree/delete/{item_id}")
    config.add_route(
        "convert_to_wms", "/{table:layers_wmts}/{id}/convert_to_wms", pregenerator=table_pregenerator
    )
    config.add_route(
        "convert_to_wmts", "/{table:layers_wms}/{id}/convert_to_wmts", pregenerator=table_pregenerator
    )

    from c2cgeoportal_commons.models.main import (
        Role,
        LayerWMS,
        LayerWMTS,
        Theme,
        LayerGroup,
        Interface,
        OGCServer,
        Functionality,
        RestrictionArea,
    )
    from c2cgeoportal_commons.models.static import User

    register_models(
        config,
        (
            ("themes", Theme),
            ("layer_groups", LayerGroup),
            ("layers_wms", LayerWMS),
            ("layers_wmts", LayerWMTS),
            ("ogc_servers", OGCServer),
            ("restriction_areas", RestrictionArea),
            ("users", User),
            ("roles", Role),
            ("functionalities", Functionality),
            ("interfaces", Interface),
        ),
    )
