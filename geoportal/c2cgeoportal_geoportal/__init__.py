# Copyright (c) 2011-2021, Camptocamp SA
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

import importlib
import logging
import os
from functools import partial
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, cast
from urllib.parse import urlsplit

import c2cgeoform
import c2cwsgiutils
import c2cwsgiutils.db
import c2cwsgiutils.index
import pyramid.config
import pyramid.renderers
import pyramid.request
import pyramid.response
import pyramid.security
import zope.event.classhandler
from c2cgeoform import Form, translator
from c2cwsgiutils.broadcast import decorator
from c2cwsgiutils.health_check import HealthCheck
from c2cwsgiutils.metrics import MemoryMapProvider, add_provider
from dogpile.cache import register_backend
from papyrus.renderers import GeoJSON
from pyramid.config import Configurator
from pyramid.httpexceptions import HTTPException
from pyramid.path import AssetResolver
from pyramid_mako import add_mako_renderer
from sqlalchemy.orm import Session, joinedload

import c2cgeoportal_commons.models
import c2cgeoportal_geoportal.views
from c2cgeoportal_commons.models import InvalidateCacheEvent
from c2cgeoportal_geoportal.lib import C2CPregenerator, caching, check_collector, checker
from c2cgeoportal_geoportal.lib.cacheversion import version_cache_buster
from c2cgeoportal_geoportal.lib.common_headers import Cache, set_common_headers
from c2cgeoportal_geoportal.lib.i18n import available_locale_names
from c2cgeoportal_geoportal.lib.metrics import (
    MemoryCacheSizeProvider,
    RasterDataSizeProvider,
    TotalPythonObjectMemoryProvider,
)
from c2cgeoportal_geoportal.lib.xsd import XSD
from c2cgeoportal_geoportal.views.entry import Entry, canvas_view

if TYPE_CHECKING:
    from c2cgeoportal_commons.models import static  # pylint: disable=ungrouped-imports,useless-suppression


LOG = logging.getLogger(__name__)

# Header predicate to accept only JSON content
JSON_CONTENT_TYPE = "Content-Type:application/json"
GEOJSON_CONTENT_TYPE = r"Content-Type:application/geo\+json"


class AssetRendererFactory:
    """Get a renderer for the assets."""

    def __init__(self, info: Any):
        del info  # unused
        self.resolver = AssetResolver("c2cgeoportal_geoportal")

    def __call__(self, value: Any, system: Dict[str, str]) -> bytes:
        del value
        asset = self.resolver.resolve(system["renderer_name"])
        return cast(bytes, asset.stream().read())


INTERFACE_TYPE_NGEO = "ngeo"
INTERFACE_TYPE_CANVAS = "canvas"


def add_interface_config(config: pyramid.config.Configurator, interface_config: Dict[str, Any]) -> None:
    """Add the interface (desktop, mobile, ...) views and routes with only the config."""
    add_interface(
        config,
        interface_config["name"],
        interface_config.get("type", INTERFACE_TYPE_NGEO),
        interface_config,
        default=interface_config.get("default", False),
    )


def add_interface(
    config: pyramid.config.Configurator,
    interface_name: str = "desktop",
    interface_type: str = INTERFACE_TYPE_NGEO,
    interface_config: Optional[Dict[str, Any]] = None,
    default: bool = False,
    **kwargs: Any,
) -> None:
    """Add the interface (desktop, mobile, ...) views and routes."""
    route = "/" if default else f"/{interface_name}"
    if interface_type == INTERFACE_TYPE_NGEO:
        add_interface_ngeo(
            config,
            route_name=interface_name,
            route=route,
            renderer=f"/etc/static-ngeo/{interface_name}.html",
            **kwargs,
        )
    elif interface_type == INTERFACE_TYPE_CANVAS:
        assert interface_config is not None
        add_interface_canvas(
            config,
            route_name=interface_name,
            route=route,
            interface_config=interface_config,
            **kwargs,
        )
    else:
        LOG.error(
            "Unknown interface type '%s', should be '%s' or '%s'.",
            interface_type,
            INTERFACE_TYPE_NGEO,
            INTERFACE_TYPE_CANVAS,
        )


def add_interface_ngeo(
    config: pyramid.config.Configurator,
    route_name: str,
    route: str,
    renderer: Optional[str] = None,
    permission: Optional[str] = None,
) -> None:
    """Add the ngeo interfaces views and routes."""

    config.add_route(route_name, route, request_method="GET")
    # Permalink theme: recover the theme for generating custom viewer.js url
    config.add_route(
        f"{route_name}theme",
        f"{route}{'' if route[-1] == '/' else '/'}theme/{{themes}}",
        request_method="GET",
    )
    config.add_view(
        Entry, attr="get_ngeo_index_vars", route_name=route_name, renderer=renderer, permission=permission
    )
    config.add_view(
        Entry,
        attr="get_ngeo_index_vars",
        route_name=f"{route_name}theme",
        renderer=renderer,
        permission=permission,
    )


def add_interface_canvas(
    config: pyramid.config.Configurator,
    route_name: str,
    route: str,
    interface_config: Dict[str, Any],
    permission: Optional[str] = None,
) -> None:
    """Add the ngeo interfaces views and routes."""

    renderer = f"/etc/geomapfish/interfaces/{route_name}.html.mako"
    config.add_route(route_name, route, request_method="GET")
    # Permalink theme: recover the theme for generating custom viewer.js URL
    config.add_route(
        f"{route_name}theme",
        f"{route}{'' if route[-1] == '/' else '/'}theme/{{themes}}",
        request_method="GET",
    )
    view = partial(canvas_view, interface_config=interface_config)
    view.__module__ = canvas_view.__module__
    config.add_view(
        view,
        route_name=route_name,
        renderer=renderer,
        permission=permission,
    )
    config.add_view(
        view,
        route_name=f"{route_name}theme",
        renderer=renderer,
        permission=permission,
    )


def add_admin_interface(config: pyramid.config.Configurator) -> None:
    """Add the administration interface views and routes."""
    if config.get_settings().get("enable_admin_interface", False):
        config.add_request_method(
            lambda request: c2cgeoportal_commons.models.DBSession(),
            "dbsession",
            reify=True,
        )
        config.add_view(c2cgeoportal_geoportal.views.add_ending_slash, route_name="admin_add_ending_slash")
        config.add_route("admin_add_ending_slash", "/admin", request_method="GET")
        config.include("c2cgeoportal_admin")


def add_getitfixed(config: pyramid.config.Configurator) -> None:
    """Add the get it fixed views and routes."""
    if config.get_settings()["getitfixed"].get("enabled", False):
        for route_name, pattern in (
            ("getitfixed_add_ending_slash", "/getitfixed"),
            ("getitfixed_admin_add_ending_slash", "/getitfixed_admin"),
        ):
            config.add_view(c2cgeoportal_geoportal.views.add_ending_slash, route_name=route_name)
            config.add_route(route_name, pattern, request_method="GET")
        config.include("getitfixed")
        # Register admin and getitfixed search paths together
        Form.set_zpt_renderer(c2cgeoform.default_search_paths, translator=translator)


def locale_negotiator(request: pyramid.request.Request) -> str:
    """Get the current language."""
    lang: str = request.params.get("lang")
    if lang is None:
        lang = request.cookies.get("_LOCALE_")
    else:
        request.response.set_cookie("_LOCALE_", lang)
    if lang is None:
        # If best_match returns None then use the default_locale_name configuration variable
        return request.accept_language.best_match(
            request.registry.settings.get("available_locale_names"),
            default_match=request.registry.settings.get("default_locale_name"),
        )
    return lang


def _match_url_start(reference: str, value: List[str]) -> bool:
    """Check that the val URL starts like the ref URL."""
    reference_parts = reference.rstrip("/").split("/")
    value_parts = value[0 : len(reference_parts)]
    return reference_parts == value_parts


def is_valid_referrer(request: pyramid.request.Request, settings: Optional[Dict[str, Any]] = None) -> bool:
    """Check if the referrer is valid."""
    if request.referer is not None:
        referrer = urlsplit(request.referer)._replace(query="", fragment="").geturl().rstrip("/").split("/")
        if settings is None:
            settings = request.registry.settings
        list_ = settings.get("authorized_referers", [])
        return any(_match_url_start(e, referrer) for e in list_)
    return True


def create_get_user_from_request(
    settings: Dict[str, Any]
) -> Callable[[pyramid.request.Request, Optional[str]], Optional["static.User"]]:
    """Get the get_user_from_request function."""

    def get_user_from_request(
        request: pyramid.request.Request, username: Optional[str] = None
    ) -> Optional["static.User"]:
        """
        Return the User object for the request.

        Return ``None`` if:
        * user is anonymous
        * it does not exist in the database
        * the referer is invalid
        """
        from c2cgeoportal_commons.models import DBSession  # pylint: disable=import-outside-toplevel
        from c2cgeoportal_commons.models.static import User  # pylint: disable=import-outside-toplevel

        if not hasattr(request, "is_valid_referer"):
            request.is_valid_referer = is_valid_referrer(request, settings)
        if not request.is_valid_referer:
            LOG.debug("Invalid referer for %s: %s", request.path_qs, repr(request.referer))
            return None

        if not hasattr(request, "user_"):
            request.user_ = None
            if username is None:
                username = request.authenticated_userid
            if username is not None:
                # We know we will need the role object of the
                # user so we use joined loading
                request.user_ = (
                    DBSession.query(User).filter_by(username=username).options(joinedload("roles")).first()
                )

        return cast(User, request.user_)

    return get_user_from_request


def set_user_validator(
    config: pyramid.config.Configurator, user_validator: Callable[[pyramid.request.Request, str, str], str]
) -> None:
    """
    Call this function to register a user validator function.

    The validator function is passed three arguments: ``request``,
    ``username``, and ``password``. The function should return the
    user name if the credentials are valid, and ``None`` otherwise.

    The validator should not do the actual authentication operation
    by calling ``remember``, this is handled by the ``login`` view.
    """

    def register() -> None:
        config.registry.validate_user = user_validator

    config.action("user_validator", register)


def default_user_validator(request: pyramid.request.Request, username: str, password: str) -> Optional[str]:
    """
    Validate the username/password.

    This is c2cgeoportal's default user validator. Return None if we are anonymous, the string to remember
    otherwise.
    """
    del request  # unused
    from c2cgeoportal_commons.models import DBSession  # pylint: disable=import-outside-toplevel
    from c2cgeoportal_commons.models.static import User  # pylint: disable=import-outside-toplevel

    user = DBSession.query(User).filter_by(username=username).first()
    if user is None:
        LOG.info('Unknown user "%s" tried to log in', username)
        return None
    if user.deactivated:
        LOG.info('Deactivated user "%s" tried to log in', username)
        return None
    if user.expired():
        LOG.info("Expired user %s tried to log in", username)
        return None
    if not user.validate_password(password):
        LOG.info('User "%s" tried to log in with bad credentials', username)
        return None
    return username


class MapserverproxyRoutePredicate:
    """
    Serve as a custom route predicate function for mapserverproxy.

    If the hide_capabilities setting is set and is true then we want to return 404s on GetCapabilities
    requests.
    """

    def __init__(self, val: Any, config: pyramid.config.Configurator) -> None:
        del val, config

    def __call__(self, context: Any, request: pyramid.request.Request) -> bool:
        del context
        hide_capabilities = request.registry.settings.get("hide_capabilities")
        if not hide_capabilities:
            return True
        params = {k.lower(): v.lower() for k, v in request.params.items()}
        return "request" not in params or params["request"] not in ("getcapabilities", "capabilities")

    @staticmethod
    def text() -> str:
        return "mapserverproxy"

    phash = text


def add_cors_route(config: pyramid.config.Configurator, pattern: str, service: str) -> None:
    """Add the OPTIONS route and view need for services supporting CORS."""

    def view(request: pyramid.request.Request) -> pyramid.response.Response:
        return set_common_headers(request, service, Cache.PRIVATE_NO)

    name = pattern + "_options"
    config.add_route(name, pattern, request_method="OPTIONS")
    config.add_view(view, route_name=name)


def error_handler(
    http_exception: HTTPException, request: pyramid.request.Request
) -> pyramid.response.Response:
    """View callable for handling all the exceptions that are not already handled."""
    LOG.warning("%s returned status code %s", request.url, http_exception.status_code)
    return set_common_headers(request, "error", Cache.PRIVATE_NO, http_exception)


def call_hook(settings: pyramid.config.Configurator, name: str, *args: Any, **kwargs: Any) -> None:
    """Call the hook defined in the settings."""
    hooks = settings.get("hooks", {})
    hook = hooks.get(name)
    if hook is None:
        return
    parts = hook.split(".")
    module = importlib.import_module(".".join(parts[0:-1]))
    function_ = getattr(module, parts[-1])
    function_(*args, **kwargs)


def includeme(config: pyramid.config.Configurator) -> None:
    """Get the Pyramid WSGI application."""
    settings = config.get_settings()

    if "available_locale_names" not in settings:
        settings["available_locale_names"] = available_locale_names()

    call_hook(settings, "after_settings", settings)

    get_user_from_request = create_get_user_from_request(settings)
    config.add_request_method(get_user_from_request, name="user", property=True)
    config.add_request_method(get_user_from_request, name="get_user")
    # Be able for an organization to override the method to use alternate:
    # - Organization roles name for the standard roles 'anonymous', 'registered' and 'intranet'.
    config.add_request_method(lambda request, role_type: role_type, name="get_organization_role")
    # - Organization print URL
    config.add_request_method(
        lambda request: request.registry.settings["print_url"], name="get_organization_print_url"
    )
    # - Organization interface name (in the config and in the admin interface)
    config.add_request_method(lambda request, interface: interface, name="get_organization_interface")

    # Configure 'locale' dir as the translation dir for c2cgeoportal app
    config.add_translation_dirs("c2cgeoportal_geoportal:locale/")

    config.include("pyramid_mako")
    config.include("c2cwsgiutils.pyramid.includeme")
    health_check = HealthCheck(config)
    config.registry["health_check"] = health_check

    metrics_config = config.registry.settings["metrics"]
    if metrics_config["memory_maps_rss"]:
        add_provider(MemoryMapProvider("rss"))
    if metrics_config["memory_maps_size"]:
        add_provider(MemoryMapProvider("size"))
    if metrics_config["memory_cache"]:
        add_provider(MemoryCacheSizeProvider(metrics_config.get("memory_cache_all", False)))
    if metrics_config["raster_data"]:
        add_provider(RasterDataSizeProvider())
    if metrics_config["total_python_object_memory"]:
        add_provider(TotalPythonObjectMemoryProvider())

    # Initialise DBSessions
    init_db_sessions(settings, config, health_check)

    checker.init(config, health_check)
    check_collector.init(config, health_check)

    # dogpile.cache configuration
    if "cache" in settings:
        register_backend("c2cgeoportal.hybrid", "c2cgeoportal_geoportal.lib.caching", "HybridRedisBackend")
        register_backend(
            "c2cgeoportal.hybridsentinel", "c2cgeoportal_geoportal.lib.caching", "HybridRedisSentinelBackend"
        )
        for name, cache_config in settings["cache"].items():
            caching.init_region(cache_config, name)

            @zope.event.classhandler.handler(InvalidateCacheEvent)  # type: ignore
            def handle(event: InvalidateCacheEvent) -> None:
                del event
                caching.invalidate_region()
                if caching.MEMORY_CACHE_DICT:
                    caching.get_region("std").delete_multi(list(caching.MEMORY_CACHE_DICT.keys()))
                caching.MEMORY_CACHE_DICT.clear()

    # Register a tween to get back the cache buster path.
    if "cache_path" not in config.get_settings():
        config.get_settings()["cache_path"] = ["static", "static-geomapfish"]
    config.add_tween("c2cgeoportal_geoportal.lib.cacheversion.CachebusterTween")
    config.add_tween("c2cgeoportal_geoportal.lib.headers.HeadersTween")

    # Bind the mako renderer to other file extensions
    add_mako_renderer(config, ".html")
    add_mako_renderer(config, ".js")

    # Add the "geojson" renderer
    config.add_renderer("geojson", GeoJSON())

    # Add the "xsd" renderer
    config.add_renderer("xsd", XSD(include_foreign_keys=True))

    # Add the set_user_validator directive, and set a default user validator
    config.add_directive("set_user_validator", set_user_validator)
    config.set_user_validator(default_user_validator)

    config.add_route("oauth2token", "/oauth/token", request_method="POST")
    config.add_route("oauth2loginform", "/oauth/login", request_method="GET")
    config.add_route("notlogin", "/notlogin", request_method="GET")

    config.add_route("dynamic", "/dynamic.json", request_method="GET")

    # Add routes to the mapserver proxy
    config.add_route_predicate("mapserverproxy", MapserverproxyRoutePredicate)
    config.add_route(
        "mapserverproxy",
        "/mapserv_proxy",
        mapserverproxy=True,
        pregenerator=C2CPregenerator(role=True),
        request_method="GET",
    )
    config.add_route(
        "mapserverproxy_post",
        "/mapserv_proxy",
        mapserverproxy=True,
        pregenerator=C2CPregenerator(role=True),
        request_method="POST",
    )
    # The tow next views are used to serve the application on the URL /mapserv_proxy/<ogc server name>
    # instead of /mapserv_proxy?ogcserver=<ogc server name>, required for QGIS server landing page
    config.add_route(
        "mapserverproxy_get_path",
        "/mapserv_proxy/{ogcserver}/*path",
        mapserverproxy=True,
        pregenerator=C2CPregenerator(role=True),
        request_method="GET",
    )
    config.add_route(
        "mapserverproxy_post_path",
        "/mapserv_proxy/{ogcserver}/*path",
        mapserverproxy=True,
        pregenerator=C2CPregenerator(role=True),
        request_method="POST",
    )
    add_cors_route(config, "/mapserv_proxy", "mapserver")

    # Add route to the tinyows proxy
    config.add_route("tinyowsproxy", "/tinyows_proxy", pregenerator=C2CPregenerator(role=True))

    # Add routes to the entry view class
    config.add_route("base", "/", static=True)
    config.add_route("loginform", "/login.html", request_method="GET")
    add_cors_route(config, "/login", "login")
    config.add_route("login", "/login", request_method="POST")
    add_cors_route(config, "/logout", "login")
    config.add_route("logout", "/logout", request_method="GET")
    add_cors_route(config, "/loginchangepassword", "login")
    config.add_route("change_password", "/loginchangepassword", request_method="POST")
    add_cors_route(config, "/loginresetpassword", "login")
    config.add_route("loginresetpassword", "/loginresetpassword", request_method="POST")
    add_cors_route(config, "/loginuser", "login")
    config.add_route("loginuser", "/loginuser", request_method="GET")
    config.add_route("testi18n", "/testi18n.html", request_method="GET")

    config.add_renderer(".map", AssetRendererFactory)
    config.add_renderer(".css", AssetRendererFactory)
    config.add_renderer(".ico", AssetRendererFactory)
    config.add_route("localejson", "/locale.json", request_method="GET")
    config.add_route("localepot", "/locale.pot", request_method="GET")

    def add_static_route(name: str, attr: str, path: str, renderer: str) -> None:
        config.add_route(name, path, request_method="GET")
        config.add_view(Entry, attr=attr, route_name=name, renderer=renderer)

    add_static_route("favicon", "favicon", "/favicon.ico", "/etc/geomapfish/static/images/favicon.ico")
    add_static_route("robot.txt", "robot_txt", "/robot.txt", "/etc/geomapfish/static/robot.txt")
    config.add_route("apijs", "/api.js", request_method="GET")
    add_static_route("apijsmap", "apijsmap", "/api.js.map", "/etc/static-ngeo/api.js.map")
    add_static_route("apicss", "apicss", "/api.css", "/etc/static-ngeo/api.css")
    add_static_route("apihelp", "apihelp", "/apihelp/index.html", "/etc/geomapfish/static/apihelp/index.html")
    c2cgeoportal_geoportal.views.add_redirect(config, "apihelp_redirect", "/apihelp.html", "apihelp")

    config.add_route("themes", "/themes", request_method="GET", pregenerator=C2CPregenerator(role=True))

    config.add_route("invalidate", "/invalidate", request_method="GET")

    # Print proxy routes
    config.add_route("printproxy", "/printproxy", request_method="HEAD")
    add_cors_route(config, "/printproxy/*all", "print")
    config.add_route(
        "printproxy_capabilities",
        "/printproxy/capabilities.json",
        request_method="GET",
        pregenerator=C2CPregenerator(role=True),
    )
    config.add_route(
        "printproxy_report_create",
        "/printproxy/report.{format}",
        request_method="POST",
        header=JSON_CONTENT_TYPE,
    )
    config.add_route("printproxy_status", "/printproxy/status/{ref}.json", request_method="GET")
    config.add_route("printproxy_cancel", "/printproxy/cancel/{ref}", request_method="DELETE")
    config.add_route("printproxy_report_get", "/printproxy/report/{ref}", request_method="GET")

    # Full-text search routes
    add_cors_route(config, "/search", "fulltextsearch")
    config.add_route("fulltextsearch", "/search", request_method="GET")

    # Access to raster data
    add_cors_route(config, "/raster", "raster")
    config.add_route("raster", "/raster", request_method="GET")

    add_cors_route(config, "/profile.json", "profile")
    config.add_route("profile.json", "/profile.json", request_method="POST")

    # Access to vector tiles
    add_cors_route(config, "/vector_tiles", "vector_tiles")
    config.add_route("vector_tiles", "/vector_tiles/{layer_name}/{z}/{x}/{y}.pbf", request_method="GET")
    # There is no view corresponding to that route, it is to be used from
    # mako templates to get the root of the "vector_tiles" web service
    config.add_route("vector_tiles_root", "/vector_tiles", request_method="HEAD")

    # Shortener
    add_cors_route(config, "/short/create", "shortener")
    config.add_route("shortener_create", "/short/create", request_method="POST")
    config.add_route("shortener_get", "/s/{ref}", request_method="GET")

    # Geometry processing
    config.add_route("difference", "/difference", request_method="POST")

    # PDF report tool
    config.add_route("pdfreport", "/pdfreport/{layername}/{ids}", request_method="GET")

    # Add routes for the "layers" web service
    add_cors_route(config, "/layers/*all", "layers")
    config.add_route("layers_count", "/layers/{layer_id:\\d+}/count", request_method="GET")
    config.add_route(
        "layers_metadata",
        "/layers/{layer_id:\\d+}/md.xsd",
        request_method="GET",
        pregenerator=C2CPregenerator(role=True),
    )
    config.add_route(
        "layers_read_many", "/layers/{layer_id:\\d+,?(\\d+,)*\\d*$}", request_method="GET"
    )  # supports URLs like /layers/1,2,3
    config.add_route("layers_read_one", "/layers/{layer_id:\\d+}/{feature_id}", request_method="GET")
    config.add_route(
        "layers_create", "/layers/{layer_id:\\d+}", request_method="POST", header=GEOJSON_CONTENT_TYPE
    )
    config.add_route(
        "layers_update",
        "/layers/{layer_id:\\d+}/{feature_id}",
        request_method="PUT",
        header=GEOJSON_CONTENT_TYPE,
    )
    config.add_route("layers_delete", "/layers/{layer_id:\\d+}/{feature_id}", request_method="DELETE")
    config.add_route(
        "layers_enumerate_attribute_values",
        "/layers/{layer_name}/values/{field_name}",
        request_method="GET",
        pregenerator=C2CPregenerator(),
    )
    # There is no view corresponding to that route, it is to be used from
    # mako templates to get the root of the "layers" web service
    config.add_route("layers_root", "/layers", request_method="HEAD")

    # Resource proxy (load external url, useful when loading non https content)
    config.add_route("resourceproxy", "/resourceproxy", request_method="GET")

    # Dev
    config.add_route("dev", "/dev/*path", request_method="GET")

    # Used memory in caches
    config.add_route("memory", "/memory", request_method="GET")

    # Scan view decorator for adding routes
    config.scan(
        ignore=[
            "c2cgeoportal_geoportal.lib",
            "c2cgeoportal_geoportal.scaffolds",
            "c2cgeoportal_geoportal.scripts",
        ]
    )

    add_admin_interface(config)
    add_getitfixed(config)

    # Add the project static view with cache buster
    config.add_static_view(
        name="static",
        path="/etc/geomapfish/static",
        cache_max_age=int(config.get_settings()["default_max_age"]),
    )
    config.add_cache_buster("/etc/geomapfish/static", version_cache_buster)

    # Add the project static view without cache buster
    config.add_static_view(
        name="static-ngeo",
        path="/etc/static-ngeo",
        cache_max_age=int(config.get_settings()["default_max_age"]),
    )

    # Add the c2cgeoportal static view with cache buster
    config.add_static_view(
        name="static-geomapfish",
        path="c2cgeoportal_geoportal:static",
        cache_max_age=int(config.get_settings()["default_max_age"]),
    )
    config.add_cache_buster("c2cgeoportal_geoportal:static", version_cache_buster)

    # Add the project static view without cache buster
    config.add_static_view(
        name="static-ngeo-dist",
        path="/opt/c2cgeoportal/geoportal/node_modules/ngeo/dist",
        cache_max_age=int(config.get_settings()["default_max_age"]),
    )

    # Handles the other HTTP errors raised by the views. Without that,
    # the client receives a status=200 without content.
    config.add_view(error_handler, context=HTTPException)

    c2cwsgiutils.index.additional_title = (
        '<div class="row"><div class="col-lg-3"><h2>GeoMapFish</h2></div><div class="col-lg">'
    )

    c2cwsgiutils.index.additional_auth.extend(
        [
            '<a href="../tiles/admin/">TileCloud chain admin</a><br>',
            '<a href="../tiles/c2c/">TileCloud chain c2c tools</a><br>',
            '<a href="../invalidate">Invalidate the cache</a><br>',
            '<a href="../memory">Memory status</a><br>',
        ]
    )
    if config.get_settings().get("enable_admin_interface", False):
        c2cwsgiutils.index.additional_noauth.append('<a href="../admin/">Admin</a><br>')

    c2cwsgiutils.index.additional_noauth.append(
        '</div></div><div class="row"><div class="col-lg-3"><h3>Interfaces</h3></div><div class="col-lg">'
    )
    c2cwsgiutils.index.additional_noauth.append('<a href="../">Default</a><br>')
    for interface in config.get_settings().get("interfaces", []):
        if not interface.get("default", False):
            c2cwsgiutils.index.additional_noauth.append(
                '<a href="../{interface}">{interface}</a><br>'.format(interface=interface["name"])
            )
    c2cwsgiutils.index.additional_noauth.append('<a href="../apihelp/index.html">API help</a><br>')
    c2cwsgiutils.index.additional_noauth.append("</div></div><hr>")


def init_db_sessions(
    settings: Dict[str, Any], config: Configurator, health_check: Optional[HealthCheck] = None
) -> None:
    """Initialize the database sessions."""
    db_chooser = settings.get("db_chooser", {})
    master_paths = [i.replace("//", "/") for i in db_chooser.get("master", [])]
    slave_paths = [i.replace("//", "/") for i in db_chooser.get("slave", [])]

    slave_prefix = "sqlalchemy_slave" if "sqlalchemy_slave.url" in settings else None

    c2cgeoportal_commons.models.DBSession, rw_bind, _ = c2cwsgiutils.db.setup_session(
        config, "sqlalchemy", slave_prefix, force_master=master_paths, force_slave=slave_paths
    )
    c2cgeoportal_commons.models.Base.metadata.bind = rw_bind
    c2cgeoportal_commons.models.DBSessions["dbsession"] = c2cgeoportal_commons.models.DBSession

    for dbsession_name, dbsession_config in settings.get("dbsessions", {}).items():  # pragma: nocover
        c2cgeoportal_commons.models.DBSessions[dbsession_name] = c2cwsgiutils.db.create_session(
            config, dbsession_name, **dbsession_config
        )

    c2cgeoportal_commons.models.Base.metadata.clear()
    from c2cgeoportal_commons.models import main  # pylint: disable=import-outside-toplevel

    if health_check is not None:
        for name, session in c2cgeoportal_commons.models.DBSessions.items():
            if name == "dbsession":
                health_check.add_db_session_check(session, at_least_one_model=main.Theme, level=1)
                alembic_ini = os.path.join(os.path.abspath(os.path.curdir), "alembic.ini")
                if os.path.exists(alembic_ini):
                    health_check.add_alembic_check(
                        session,
                        alembic_ini_path=alembic_ini,
                        name="main",
                        version_schema=settings["schema"],
                        level=1,
                    )
                    health_check.add_alembic_check(
                        session,
                        alembic_ini_path=alembic_ini,
                        name="static",
                        version_schema=settings["schema_static"],
                        level=1,
                    )
            else:

                def check(session_: Session) -> None:
                    session_.execute("SELECT 1")

                health_check.add_db_session_check(session, query_cb=check, level=2)
