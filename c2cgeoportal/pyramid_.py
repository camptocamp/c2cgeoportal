# -*- coding: utf-8 -*-

# Copyright (c) 2011-2017, Camptocamp SA
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

import logging
import sqlalchemy
import sqlahelper
import pyramid_tm
import mimetypes
import c2c.template
from urlparse import urlsplit
import simplejson as json
from socket import gethostbyname, gaierror
from ipcalc import IP, Network
import importlib

from pyramid_mako import add_mako_renderer
from pyramid.interfaces import IStaticURLInfo
from pyramid.httpexceptions import HTTPException

from papyrus.renderers import GeoJSON, XSD

import c2cgeoportal
from c2cgeoportal import stats
from c2cgeoportal.resources import FAModels
from c2cgeoportal.lib import dbreflection, get_setting, caching, \
    C2CPregenerator, MultiDomainStaticURLInfo

log = logging.getLogger(__name__)

# Header predicate to accept only JSON content
# OL/cgxp are not setting the correct content type for JSON. We have to accept
# XML as well even though JSON is actually send.
JSON_CONTENT_TYPE = "Content-Type:application/(?:json|xml)"


class DecimalJSON:
    def __init__(self, jsonp_param_name="callback"):
        self.jsonp_param_name = jsonp_param_name

    def __call__(self, info):
        def _render(value, system):
            ret = json.dumps(value, use_decimal=True)
            request = system.get("request")
            if request is not None:
                callback = request.params.get(self.jsonp_param_name)
                if callback is None:
                    request.response.content_type = "application/json"
                else:
                    request.response.content_type = "text/javascript"
                    ret = "{callback!s}({json!s});".format(
                        callback=callback,
                        json=ret
                    )
            return ret
        return _render


INTERFACE_TYPE_CGXP = "cgxp"
INTERFACE_TYPE_NGEO = "ngeo"
INTERFACE_TYPE_NGEO_CATALOGUE = "ngeo"


def add_interface(
    config, interface_name="desktop", interface_type=INTERFACE_TYPE_CGXP, **kwargs
):  # pragma: no cover
    if interface_type == INTERFACE_TYPE_CGXP:
        add_interface_cgxp(
            config,
            interface_name=interface_name,
            route_names=(interface_name, interface_name + ".js"),
            routes=("/{0!s}".format(interface_name), "/{0!s}.js".format(interface_name)),
            renderers=("/{0!s}.html".format(interface_name), "/{0!s}.js".format(interface_name)),
            **kwargs
        )

    elif interface_type == INTERFACE_TYPE_NGEO:
        route = "/{0!s}".format(interface_name)
        add_interface_ngeo(
            config,
            interface_name=interface_name,
            route_name=interface_name,
            route=route,
            renderer="/{0!s}.html".format(interface_name),
            **kwargs
        )


def add_interface_cgxp(
        config, interface_name, route_names, routes, renderers, permission=None):  # pragma: no cover
    # Cannot be at the header to don"t load the model too early
    from c2cgeoportal.views.entry import Entry

    def add_interface(f):
        def new_f(root, request):
            request.interface_name = interface_name
            return f(root, request)
        return new_f

    config.add_route(route_names[0], routes[0])
    config.add_view(
        Entry,
        decorator=add_interface,
        attr="get_cgxp_index_vars",
        route_name=route_names[0],
        renderer=renderers[0],
        permission=permission
    )
    # permalink theme: recover the theme for generating custom viewer.js url
    config.add_route(
        "{0!s}theme".format(route_names[0]),
        "{0!s}{1!s}theme/{{themes}}".format(routes[0], "" if routes[0][-1] == "/" else "/"),
    )
    config.add_view(
        Entry,
        decorator=add_interface,
        attr="get_cgxp_permalinktheme_vars",
        route_name="{0!s}theme".format(route_names[0]),
        renderer=renderers[0],
        permission=permission
    )
    config.add_route(
        route_names[1], routes[1],
        request_method="GET",
        pregenerator=C2CPregenerator(role=True),
    )
    config.add_view(
        Entry,
        decorator=add_interface,
        attr="get_cgxp_viewer_vars",
        route_name=route_names[1],
        renderer=renderers[1],
        permission=permission
    )


ngeo_static_init = False


def add_interface_ngeo(
        config, interface_name, route_name, route, renderer, permission=None):  # pragma: no cover
    # Cannot be at the header to do not load the model too early
    from c2cgeoportal.views.entry import Entry

    def add_interface(f):
        def new_f(root, request):
            request.interface_name = interface_name
            return f(root, request)
        return new_f

    config.add_route(route_name, route, request_method="GET")
    config.add_view(
        Entry,
        decorator=add_interface,
        attr="get_ngeo_index_vars",
        route_name=route_name,
        renderer=renderer,
        permission=permission
    )
    # permalink theme: recover the theme for generating custom viewer.js url
    config.add_route(
        "{0!s}theme".format(route_name),
        "{0!s}{1!s}theme/{{themes}}".format(route, "" if route[-1] == "/" else "/"),
        request_method="GET",
    )
    config.add_view(
        Entry,
        decorator=add_interface,
        attr="get_ngeo_permalinktheme_vars",
        route_name="{0!s}theme".format(route_name),
        renderer=renderer,
        permission=permission
    )

    global ngeo_static_init
    if not ngeo_static_init:
        add_static_view_ngeo(config)
        ngeo_static_init = True


def add_static_view_ngeo(config):  # pragma: no cover
    """ Add the project static view for ngeo """
    package = config.get_settings()["package"]
    _add_static_view(config, "static-ngeo", "{0!s}:static-ngeo".format(package))
    config.override_asset(
        to_override="c2cgeoportal:project/",
        override_with="{0!s}:static-ngeo/".format(package)
    )
    config.add_static_view(
        name=package,
        path="{0!s}:static".format(package),
        cache_max_age=int(config.get_settings()["default_max_age"])
    )

    config.add_static_view("node_modules", config.get_settings().get("node_modules_path"))
    config.add_static_view("closure", config.get_settings().get("closure_library_path"))

    mimetypes.add_type("text/css", ".less")


def add_admin_interface(config):
    if config.get_settings().get("enable_admin_interface", False):
        config.formalchemy_admin(
            route_name="admin",
            package=config.get_settings()["package"],
            view="fa.jquery.pyramid.ModelView",
            factory=FAModels
        )


def add_static_view(config):
    """ Add the project static view for CGXP """
    package = config.get_settings()["package"]
    _add_static_view(config, "static-cgxp", "{0!s}:static".format(package))
    config.override_asset(
        to_override="c2cgeoportal:project/",
        override_with="{0!s}:static/".format(package)
    )


CACHE_PATH = []


def _add_static_view(config, name, path):
    from c2cgeoportal.lib.cacheversion import version_cache_buster
    config.add_static_view(
        name=name,
        path=path,
        cache_max_age=int(config.get_settings()["default_max_age"]),
    )
    config.add_cache_buster(path, version_cache_buster)
    CACHE_PATH.append(unicode(name))


def locale_negotiator(request):
    lang = request.params.get("lang")
    if lang is None:
        # if best_match returns None then use the default_locale_name configuration variable
        return request.accept_language.best_match(
            request.registry.settings.get("available_locale_names"),
            default_match=request.registry.settings.get("default_locale_name"))
    return lang


def _match_url_start(ref, val):
    """
    Checks that the val URL starts like the ref URL.
    """
    ref_parts = ref.rstrip("/").split("/")
    val_parts = val.rstrip("/").split("/")[0:len(ref_parts)]
    return ref_parts == val_parts


def _is_valid_referer(request, settings):
    if request.referer is not None:
        list = settings.get("authorized_referers", [])
        return any(_match_url_start(x, request.referer) for x in list)
    else:
        return request.method == "GET"


def _create_get_user_from_request(settings):
    def get_user_from_request(request, username=None):
        """ Return the User object for the request.

        Return ``None`` if:
        * user is anonymous
        * it does not exist in the database
        * the referer is invalid
        """
        from c2cgeoportal.models import DBSession, User

        if not hasattr(request, "_is_valid_referer"):
            request._is_valid_referer = _is_valid_referer(request, settings)
        if not request._is_valid_referer:
            log.warning("Invalid referer for %s: %s", request.path_qs,
                        repr(request.referer))
            return None

        if not hasattr(request, "_user"):
            request._user = None
            if username is None:
                username = request.authenticated_userid
            if username is not None:
                # We know we will need the role object of the
                # user so we use joined loading
                request._user = DBSession.query(User) \
                    .filter_by(username=username) \
                    .first()

        return request._user
    return get_user_from_request


def set_user_validator(config, user_validator):
    """ Call this function to register a user validator function.

    The validator function is passed three arguments: ``request``,
    ``username``, and ``password``. The function should return the
    user name if the credentials are valid, and ``None`` otherwise.

    The validator should not do the actual authentication operation
    by calling ``remember``, this is handled by the ``login`` view.
    """
    def register():
        config.registry.validate_user = user_validator
    config.action("user_validator", register)


def default_user_validator(request, username, password):
    """
    Validate the username/password. This is c2cgeoportal's
    default user validator.
    Return none if we are anonymous, the string to remember otherwise.
    """
    from c2cgeoportal.models import DBSession, User
    user = DBSession.query(User).filter_by(username=username).first()
    return username if user and user.validate_password(password) else None


class OgcproxyRoutePredicate:
    """ Serve as a custom route predicate function for ogcproxy.
    We do not want the OGC proxy to be used to reach the app's
    mapserv script. We just return False if the url includes
    "mapserv". It is rather drastic, but works for us. """

    def __init__(self, val, config):
        self.private_networks = [
            Network("127.0.0.0/8"),
            Network("10.0.0.0/8"),
            Network("172.16.0.0/12"),
            Network("192.168.0.0/16"),
        ]

    def __call__(self, context, request):
        url = request.params.get("url")
        if url is None:
            return False

        parts = urlsplit(url)
        try:
            ip = IP(gethostbyname(parts.netloc))
        except gaierror as e:
            log.info("Unable to get host name for {0!s}: {1!s}".format(url, e))
            return False
        for net in self.private_networks:
            if ip in net:
                return False
        return True

    @staticmethod
    def phash():  # pragma: no cover
        return ""


class MapserverproxyRoutePredicate:
    """ Serve as a custom route predicate function for mapserverproxy.
    If the hide_capabilities setting is set and is true then we want to
    return 404s on GetCapabilities requests."""

    def __init__(self, val, config):
        pass

    def __call__(self, context, request):
        hide_capabilities = request.registry.settings.get("hide_capabilities")
        if not hide_capabilities:
            return True
        params = dict(
            (k.lower(), unicode(v).lower()) for k, v in request.params.iteritems()
        )
        return "request" not in params or params["request"] != u"getcapabilities"

    def phash(self):
        return ""


def add_cors_route(config, pattern, service):
    """
    Add the OPTIONS route and view need for services supporting CORS.
    """
    def view(request):  # pragma: no cover
        from c2cgeoportal.lib.caching import set_common_headers, NO_CACHE
        return set_common_headers(request, service, NO_CACHE)

    name = pattern + "_options"
    config.add_route(name, pattern, request_method="OPTIONS")
    config.add_view(view, route_name=name)


def error_handler(http_exception, request):  # pragma: no cover
    """
    View callable for handling all the exceptions that are not already handled.
    """
    log.warning("%s returned status code %s", request.url,
                http_exception.status_code)
    return caching.set_common_headers(
        request, "error", caching.NO_CACHE, http_exception, vary=True
    )


def call_hook(settings, name, *args, **kwargs):
    hooks = settings.get("hooks", {})
    hook = hooks.get(name)
    if hook is None:
        return
    parts = hook.split(".")
    module = importlib.import_module(".".join(parts[0:-1]))
    function = getattr(module, parts[-1])
    function(*args, **kwargs)


def includeme(config):
    """ This function returns a Pyramid WSGI application.
    """

    # update the settings object from the YAML application config file
    settings = config.get_settings()
    settings.update(c2c.template.get_config(settings.get("app.cfg")))

    call_hook(settings, "after_settings", settings)

    get_user_from_request = _create_get_user_from_request(settings)
    config.add_request_method(get_user_from_request, name="user", property=True)
    config.add_request_method(get_user_from_request, name="get_user")

    # configure 'locale' dir as the translation dir for c2cgeoportal app
    config.add_translation_dirs("c2cgeoportal:locale/")

    # initialize database
    engine = sqlalchemy.engine_from_config(
        settings,
        "sqlalchemy.")
    sqlahelper.add_engine(engine)
    config.include(pyramid_tm.includeme)
    config.include("pyramid_closure")

    if "sqlalchemy_slave.url" in settings and \
            settings["sqlalchemy.url"] != settings["sqlalchemy_slave.url"]:  # pragma: nocover
        # Setup a slave DB connection and add a tween to switch between it and the default one.
        log.info("Using a slave DB for reading")
        engine_slave = sqlalchemy.engine_from_config(config.get_settings(), "sqlalchemy_slave.")
        sqlahelper.add_engine(engine_slave, name="slave")
        config.add_tween("c2cgeoportal.models.db_chooser_tween_factory",
                         over="pyramid_tm.tm_tween_factory")

    # initialize the dbreflection module
    dbreflection.init(engine)

    # dogpile.cache configuration
    caching.init_region(settings["cache"])
    caching.invalidate_region()

    # Register a tween to get back the cache buster path.
    config.add_tween("c2cgeoportal.lib.cacheversion.CachebusterTween")

    # bind the mako renderer to other file extensions
    add_mako_renderer(config, ".html")
    add_mako_renderer(config, ".js")
    config.include("pyramid_chameleon")

    # add the "geojson" renderer
    config.add_renderer("geojson", GeoJSON())

    # add decimal json renderer
    config.add_renderer("decimaljson", DecimalJSON())

    # add the "xsd" renderer
    config.add_renderer("xsd", XSD(
        sequence_callback=dbreflection._xsd_sequence_callback
    ))

    # add the set_user_validator directive, and set a default user
    # validator
    config.add_directive("set_user_validator", set_user_validator)
    config.set_user_validator(default_user_validator)

    if settings.get("ogcproxy_enable", False):  # pragma: no cover
        # add an OGCProxy view
        config.add_route_predicate("ogc_server", OgcproxyRoutePredicate)
        config.add_route(
            "ogcproxy", "/ogcproxy",
            ogc_server=True
        )
        config.add_view("papyrus_ogcproxy.views:ogcproxy", route_name="ogcproxy")

    # add routes to the mapserver proxy
    config.add_route_predicate("mapserverproxy", MapserverproxyRoutePredicate)
    config.add_route(
        "mapserverproxy", "/mapserv_proxy",
        mapserverproxy=True, pregenerator=C2CPregenerator(role=True),
    )

    # add route to the tinyows proxy
    config.add_route(
        "tinyowsproxy", "/tinyows_proxy",
        pregenerator=C2CPregenerator(role=True),
    )

    # add routes to csv view
    config.add_route("csvecho", "/csv", request_method="POST")

    # add route to the export GPX/KML view
    config.add_route("exportgpxkml", "/exportgpxkml")

    # add routes to the echo service
    config.add_route("echo", "/echo", request_method="POST")

    # add routes to the entry view class
    config.add_route("base", "/", static=True)
    config.add_route("loginform", "/login.html", request_method="GET")
    add_cors_route(config, "/login", "login")
    config.add_route("login", "/login", request_method="POST")
    add_cors_route(config, "/logout", "login")
    config.add_route("logout", "/logout", request_method="GET")
    add_cors_route(config, "/loginchange", "login")
    config.add_route("loginchange", "/loginchange", request_method="POST")
    add_cors_route(config, "/loginresetpassword", "login")
    config.add_route("loginresetpassword", "/loginresetpassword", request_method="POST")
    add_cors_route(config, "/loginuser", "login")
    config.add_route("loginuser", "/loginuser", request_method="GET")
    config.add_route("testi18n", "/testi18n.html", request_method="GET")
    config.add_route("apijs", "/api.js", request_method="GET")
    config.add_route("xapijs", "/xapi.js", request_method="GET")
    config.add_route("apihelp", "/apihelp.html", request_method="GET")
    config.add_route("xapihelp", "/xapihelp.html", request_method="GET")
    config.add_route(
        "themes", "/themes",
        request_method="GET",
        pregenerator=C2CPregenerator(role=True),
    )
    config.add_route("invalidate", "/invalidate", request_method="GET")

    # checker routes, Checkers are web services to test and assess that
    # the application is correctly functioning.
    # These web services are used by tools like (nagios).
    config.add_route("checker_routes", "/checker_routes", request_method="GET")
    config.add_route("checker_lang_files", "/checker_lang_files", request_method="GET")
    config.add_route("checker_pdf", "/checker_pdf", request_method="GET")
    config.add_route("checker_pdf3", "/checker_pdf3", request_method="GET")
    config.add_route("checker_fts", "/checker_fts", request_method="GET")
    config.add_route("checker_theme_errors", "/checker_theme_errors", request_method="GET")
    config.add_route("checker_phantomjs", "/checker_phantomjs", request_method="GET")
    # collector
    config.add_route("check_collector", "/check_collector", request_method="GET")

    # print proxy routes
    config.add_route("printproxy", "/printproxy", request_method="HEAD")
    add_cors_route(config, "/printproxy/*all", "print")
    config.add_route(
        "printproxy_capabilities", "/printproxy/capabilities.json",
        request_method="GET", pregenerator=C2CPregenerator(role=True),
    )
    config.add_route(
        "printproxy_report_create", "/printproxy/report.{format}",
        request_method="POST", header=JSON_CONTENT_TYPE
    )
    config.add_route(
        "printproxy_status", "/printproxy/status/{ref}.json",
        request_method="GET"
    )
    config.add_route(
        "printproxy_cancel", "/printproxy/cancel/{ref}",
        request_method="DELETE"
    )
    config.add_route(
        "printproxy_report_get", "/printproxy/report/{ref}",
        request_method="GET"
    )
    # v2
    config.add_route(
        "printproxy_info", "/printproxy/info.json",
        request_method="GET",
        pregenerator=C2CPregenerator(role=True),
    )
    config.add_route(
        "printproxy_create", "/printproxy/create.json",
        request_method="POST",
    )
    config.add_route(
        "printproxy_get", "/printproxy/{file}.printout",
        request_method="GET",
    )

    # full text search routes
    add_cors_route(config, "/fulltextsearch", "fulltextsearch")
    config.add_route("fulltextsearch", "/fulltextsearch")

    # Access to raster data
    add_cors_route(config, "/raster", "raster")
    config.add_route("raster", "/raster", request_method="GET")

    add_cors_route(config, "/profile.{ext}", "profile")
    config.add_route("profile.csv", "/profile.csv", request_method="POST")
    config.add_route("profile.json", "/profile.json", request_method="POST")

    # shortener
    add_cors_route(config, "/short/create", "shortner")
    config.add_route("shortener_create", "/short/create", request_method="POST")
    config.add_route("shortener_get", "/short/{ref}", request_method="GET")

    # Geometry processing
    config.add_route("difference", "/difference", request_method="POST")

    # PDF report tool
    config.add_route("pdfreport", "/pdfreport/{layername}/{id}", request_method="GET")

    # add routes for the "layers" web service
    add_cors_route(config, "/layers/*all", "layers")
    config.add_route(
        "layers_count", "/layers/{layer_id:\\d+}/count",
        request_method="GET"
    )
    config.add_route(
        "layers_metadata", "/layers/{layer_id:\\d+}/md.xsd",
        request_method="GET",
        pregenerator=C2CPregenerator(role=True),
    )
    config.add_route(
        "layers_read_many",
        "/layers/{layer_id:\\d+,?(\\d+,)*\\d*$}",
        request_method="GET")  # supports URLs like /layers/1,2,3
    config.add_route(
        "layers_read_one", "/layers/{layer_id:\\d+}/{feature_id}",
        request_method="GET")
    config.add_route(
        "layers_create", "/layers/{layer_id:\\d+}",
        request_method="POST", header=JSON_CONTENT_TYPE)
    config.add_route(
        "layers_update", "/layers/{layer_id:\\d+}/{feature_id}",
        request_method="PUT", header=JSON_CONTENT_TYPE)
    config.add_route(
        "layers_delete", "/layers/{layer_id:\\d+}/{feature_id}",
        request_method="DELETE")
    config.add_route(
        "layers_enumerate_attribute_values",
        "/layers/{layer_name}/values/{field_name}",
        request_method="GET",
        pregenerator=C2CPregenerator(),
    )
    # there is no view corresponding to that route, it is to be used from
    # mako templates to get the root of the "layers" web service
    config.add_route("layers_root", "/layers/", request_method="HEAD")

    # Resource proxy (load external url, useful when loading non https content)
    config.add_route("resourceproxy", "/resourceproxy", request_method="GET")

    # pyramid_formalchemy's configuration
    config.include("pyramid_formalchemy")
    config.include("fa.jquery")

    # define the srid, schema and parentschema
    # as global variables to be usable in the model
    c2cgeoportal.srid = settings["srid"]
    c2cgeoportal.schema = settings["schema"]
    c2cgeoportal.parentschema = settings["parentschema"]
    c2cgeoportal.formalchemy_default_zoom = get_setting(
        settings,
        ("admin_interface", "map_zoom"),
        c2cgeoportal.formalchemy_default_zoom
    )
    c2cgeoportal.formalchemy_default_x = get_setting(
        settings,
        ("admin_interface", "map_x"),
        c2cgeoportal.formalchemy_default_x
    )
    c2cgeoportal.formalchemy_default_y = get_setting(
        settings,
        ("admin_interface", "map_y"),
        c2cgeoportal.formalchemy_default_y
    )
    c2cgeoportal.formalchemy_available_functionalities = get_setting(
        settings,
        ("admin_interface", "available_functionalities"),
        c2cgeoportal.formalchemy_available_functionalities
    )
    c2cgeoportal.formalchemy_available_metadata = get_setting(
        settings,
        ("admin_interface", "available_metadata"),
        c2cgeoportal.formalchemy_available_metadata
    )
    c2cgeoportal.formalchemy_available_metadata = [
        e if isinstance(e, basestring) else e.get("name")
        for e in c2cgeoportal.formalchemy_available_metadata
    ]

    config.add_route("checker_all", "/checker_all", request_method="GET")

    config.add_route("version_json", "/version.json", request_method="GET")

    stats.init(config)

    # scan view decorator for adding routes
    config.scan(ignore=["c2cgeoportal.tests", "c2cgeoportal.scripts"])

    if "subdomains" in settings:  # pragma: no cover
        config.registry.registerUtility(
            MultiDomainStaticURLInfo(), IStaticURLInfo)

    # add the static view (for static resources)
    _add_static_view(config, "static", "c2cgeoportal:static")
    _add_static_view(config, "project", "c2cgeoportal:project")

    add_admin_interface(config)
    add_static_view(config)

    # Handles the other HTTP errors raised by the views. Without that,
    # the client receives a status=200 without content.
    config.add_view(error_handler, context=HTTPException)

    _log_versions(settings)


def _log_versions(settings):
    package = settings.get("package")
    if package is not None:
        try:
            import c2cgeoportal.version
            project_info = importlib.import_module(package + ".version").INFO
            c2c_info = c2cgeoportal.version.INFO
            log.warning("Starting WSGI for %s version %s (%s) with c2cgeoportal version %s (%s)",
                        package, project_info["git_tag"], project_info["git_hash"][0:8],
                        c2c_info["git_tag"], c2c_info["git_hash"][0:8])
        except:  # pragma: nocover
            pass  # In some cases, we do not have the version.py file
