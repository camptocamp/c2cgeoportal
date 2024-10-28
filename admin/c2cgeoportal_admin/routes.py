# Copyright (c) 2017-2024, Camptocamp SA
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# The views and conclusions contained in the software and documentation are those
# of the authors and should not be interpreted as representing official policies,
# either expressed or implied, of the FreeBSD Project.


from c2cgeoform.routes import register_route, register_routes


def includeme(config):
    """Initialize the Pyramid routes."""
    config.add_static_view("c2cgeoportal_admin_node_modules", "c2cgeoportal_admin:node_modules")
    config.override_asset(
        to_override="c2cgeoportal_admin:node_modules/", override_with="/opt/c2cgeoportal/admin/node_modules"
    )
    # Because c2cgeoform widgets target {root_package}:node_modules/...
    asset_spec = f"{config.root_package.__name__}:node_modules/"
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
    register_route(
        config, "ogcserver_synchronize", "/{application:admin}/{table:ogc_servers}/{id}/synchronize"
    )

    from c2cgeoportal_commons.models.main import (  # pylint: disable=import-outside-toplevel
        Functionality,
        Interface,
        LayerCOG,
        LayerGroup,
        LayerVectorTiles,
        LayerWMS,
        LayerWMTS,
        Log,
        OGCServer,
        RestrictionArea,
        Role,
        Theme,
    )
    from c2cgeoportal_commons.models.static import (  # pylint: disable=import-outside-toplevel
        OAuth2Client,
        User,
    )

    authentication_configuration = config.registry.settings.get("authentication", {})
    oidc_configuration = authentication_configuration.get("openid_connect", {})
    oidc_enabled = oidc_configuration.get("enabled", False)
    oidc_provide_roles = oidc_configuration.get("provide_roles", False)
    oauth2_configuration = authentication_configuration.get("oauth2", {})
    oauth2_enabled = oauth2_configuration.get("enabled", not oidc_enabled)

    visible_routes = [
        ("themes", Theme),
        ("layer_groups", LayerGroup),
        ("layers_wms", LayerWMS),
        ("layers_wmts", LayerWMTS),
        ("layers_vectortiles", LayerVectorTiles),
        ("layers_cog", LayerCOG),
        ("ogc_servers", OGCServer),
        ("restriction_areas", RestrictionArea),
        *([("users", User)] if not oidc_enabled or not oidc_provide_roles else []),
        ("roles", Role),
        ("functionalities", Functionality),
        ("interfaces", Interface),
        *([("oauth2_clients", OAuth2Client)] if oauth2_enabled else []),
        ("logs", Log),
    ]

    admin_interface_config = config.registry.settings["admin_interface"]

    # Exclude pages
    visible_routes = [
        (url_path, model)
        for (url_path, model) in visible_routes
        if url_path not in admin_interface_config.get("exclude_pages", [])
    ]

    # Include pages
    for spec in admin_interface_config.get("include_pages", []):
        mytuple = (spec["url_path"], config.maybe_dotted(spec["model"]))
        visible_routes.append(mytuple)

    config.add_c2cgeoform_application("admin", visible_routes)
    register_routes(config)
