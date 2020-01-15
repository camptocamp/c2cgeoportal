from c2cgeoform.routes import register_route, register_routes


def includeme(config):
    config.add_static_view("c2cgeoportal_admin_node_modules", "c2cgeoportal_admin:node_modules")
    config.override_asset(
        to_override="c2cgeoportal_admin:node_modules/", override_with="/opt/c2cgeoportal/admin/node_modules"
    )
    # Because c2cgeoform widgets target {root_package}:node_modules/...
    asset_spec = "{}:node_modules/".format(config.root_package.__name__)
    config.add_static_view("root_package_node_modules", asset_spec)
    config.override_asset(to_override=asset_spec, override_with="/opt/c2cgeoportal/admin/node_modules")

    config.add_static_view("admin_static", "c2cgeoportal_admin:static", cache_max_age=3600)

    register_route(config, "admin", "/{application:admin}/")
    register_route(config, "layertree", "/{application:admin}/layertree")
    register_route(config, "layertree_children", "/{application:admin}/layertree/children")
    register_route(config, "layertree_ordering", "/{application:admin}/layertree/ordering")
    register_route(config, "layertree_unlink", "/{application:admin}/layertree/unlink/{group_id}/{item_id}")
    register_route(config, "layertree_delete", "/{application:admin}/layertree/delete/{item_id}")
    register_route(config, "convert_to_wms", "/{application:admin}/{table:layers_wmts}/{id}/convert_to_wms")
    register_route(config, "convert_to_wmts", "/{application:admin}/{table:layers_wms}/{id}/convert_to_wmts")

    from c2cgeoportal_commons.models.main import (  # pylint: disable=import-outside-toplevel
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
    from c2cgeoportal_commons.models.static import User  # pylint: disable=import-outside-toplevel

    visible_routes = [
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
    ]

    admin_interface_config = config.registry.settings["admin_interface"]

    # Include pages
    for url_path, model in admin_interface_config.get("include_pages", []):
        mytuple = (url_path, config.maybe_dotted(model))
        visible_routes.append(mytuple)

    # Exclude pages
    visible_routes = [
        (url_path, model)
        for (url_path, model) in visible_routes
        if url_path not in admin_interface_config.get("exclude_pages", [])
    ]

    config.add_c2cgeoform_application("admin", visible_routes)
    register_routes(config)
