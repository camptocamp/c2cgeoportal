# -*- coding: utf-8 -*-

# Copyright (c) 2011-2019, Camptocamp SA
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

import binascii
import time
import logging
import os
import re
from urllib.parse import urlsplit
from socket import gethostbyname, gaierror
import importlib

import simplejson as json
from ipcalc import IP, Network
from Crypto.Cipher import AES

import zope.event.classhandler
from pyramid.config import Configurator
from pyramid.interfaces import IStaticURLInfo
from pyramid.httpexceptions import HTTPException
from pyramid.path import AssetResolver
import pyramid.security
from pyramid_mako import add_mako_renderer
from papyrus.renderers import GeoJSON
from sqlalchemy.orm import Session

import c2cwsgiutils
import c2cwsgiutils.db
import c2cwsgiutils.index
from c2cwsgiutils.health_check import HealthCheck

import c2cgeoportal_commons.models
from c2cgeoportal_geoportal.lib.xsd import XSD
from c2cgeoportal_geoportal.lib import dbreflection, caching, \
    C2CPregenerator, MultiDomainStaticURLInfo, checker, check_collector
import c2cgeoportal_geoportal.views


LOG = logging.getLogger(__name__)

# Header predicate to accept only JSON content
JSON_CONTENT_TYPE = "Content-Type:application/json"
GEOJSON_CONTENT_TYPE = r'Content-Type:application/geo\+json'


class DecimalJSON:
    def __call__(self, info):
        def _render(value, system):
            ret = json.dumps(value, use_decimal=True)
            request = system.get("request")
            if request is not None:
                request.response.content_type = "application/json"
            return ret
        return _render


class AssetRendererFactory:
    def __init__(self, info):
        del info  # unused
        self.resolver = AssetResolver('c2cgeoportal_geoportal')

    def __call__(self, value, system):
        asset = self.resolver.resolve(system['renderer_name'])
        return asset.stream().read()


INTERFACE_TYPE_NGEO = "ngeo"


def add_interface(
    config, interface_name="desktop", interface_type=INTERFACE_TYPE_NGEO, default=False, **kwargs
):  # pragma: no cover
    del interface_type  # unused
    route = "/" if default else "/{}".format(interface_name)
    add_interface_ngeo(
        config,
        route_name=interface_name,
        route=route,
        renderer="{}_geoportal:static-ngeo/build/{}.html".format(
            config.get_settings()['package'], interface_name
        ),
        **kwargs
    )


def add_interface_ngeo(config, route_name, route, renderer=None, permission=None):  # pragma: no cover
    # Cannot be at the header to do not load the model too early
    from c2cgeoportal_geoportal.views.entry import Entry

    config.add_route(route_name, route, request_method="GET")
    config.add_view(
        Entry,
        attr="get_ngeo_index_vars",
        route_name=route_name,
        renderer=renderer,
        permission=permission
    )
    # Permalink theme: recover the theme for generating custom viewer.js url
    config.add_route(
        "{}theme".format(route_name),
        "{}{}theme/{{themes}}".format(route, "" if route[-1] == "/" else "/"),
        request_method="GET",
    )
    config.add_view(
        Entry,
        attr="get_ngeo_index_vars",
        route_name="{}theme".format(route_name),
        renderer=renderer,
        permission=permission
    )


def add_admin_interface(config):
    if config.get_settings().get('enable_admin_interface', False):
        config.add_request_method(
            # pylint: disable=not-callable
            lambda request: c2cgeoportal_commons.models.DBSession(), 'dbsession', reify=True
        )
        config.add_view(c2cgeoportal_geoportal.views.add_ending_slash, route_name='admin_add_ending_slash')
        config.add_route('admin_add_ending_slash', '/admin', request_method='GET')
        config.include('c2cgeoportal_admin', route_prefix='/admin')


def locale_negotiator(request):
    lang = request.params.get("lang")
    if lang is None:
        lang = request.cookies.get('_LOCALE_')
    else:
        request.response.set_cookie('_LOCALE_', lang)
    if lang is None:
        # if best_match returns None then use the default_locale_name configuration variable
        return request.accept_language.best_match(
            request.registry.settings.get("available_locale_names"),
            default_match=request.registry.settings.get("default_locale_name"))
    return lang


def _match_url_start(reference, value):
    """
    Checks that the val URL starts like the ref URL.
    """
    reference_parts = reference.rstrip("/").split("/")
    value_parts = value[0:len(reference_parts)]
    return reference_parts == value_parts


def is_valid_referer(request, settings=None):
    if request.referer is not None:
        referer = urlsplit(request.referer)._replace(query="", fragment="").geturl().rstrip("/").split("/")
        if settings is None:
            settings = request.registry.settings
        list_ = settings.get("authorized_referers", [])
        return any(_match_url_start(e, referer) for e in list_)
    else:
        return True


def create_get_user_from_request(settings):
    def get_user_from_request(request, username=None):
        """ Return the User object for the request.

        Return ``None`` if:
        * user is anonymous
        * it does not exist in the database
        * the referer is invalid
        """
        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.static import User

        try:
            if request.method == 'GET' and "auth" in request.params:
                auth_enc = request.params.get("auth")

                if auth_enc is not None:
                    urllogin = request.registry.settings.get("urllogin", {})
                    aeskey = urllogin.get("aes_key")
                    if aeskey is None:  # pragma: nocover
                        raise Exception("urllogin is not configured")
                    now = int(time.time())
                    data = binascii.unhexlify(auth_enc.encode('ascii'))
                    nonce = data[0:16]
                    tag = data[16:32]
                    ciphertext = data[32:]
                    cipher = AES.new(aeskey.encode("ascii"), AES.MODE_EAX, nonce)
                    auth = json.loads(cipher.decrypt_and_verify(ciphertext, tag).decode("utf-8"))

                    if "t" in auth and "u" in auth and "p" in auth:
                        timestamp = int(auth["t"])
                        if now < timestamp and request.registry.validate_user(
                            request, auth["u"], auth["p"]
                        ):
                            headers = pyramid.security.remember(request, auth["u"])
                            request.response.headerlist.extend(headers)
        except Exception as e:
            LOG.error("URL login error: %s.", e, exc_info=True)

        if not hasattr(request, "is_valid_referer"):
            request.is_valid_referer = is_valid_referer(request, settings)
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
                request.user_ = DBSession.query(User) \
                    .filter_by(username=username) \
                    .first()

        return request.user_
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
    Return None if we are anonymous, the string to remember otherwise.
    """
    del request  # unused
    from c2cgeoportal_commons.models import DBSession
    from c2cgeoportal_commons.models.static import User
    user = DBSession.query(User).filter_by(username=username).first()
    if user is None:
        LOG.info('Unknow user "%s" tried to log in', username)
        return None
    if user.deactivated:
        LOG.info('Deactivated user "%s" tried to log in', username)
        return None
    if user.expired():
        LOG.info('Expired user %s tried to log in', username)
        return None
    if not user.validate_password(password):
        LOG.info('User "%s" tried to log in with bad credentials', username)
        return None
    return username


class OgcproxyRoutePredicate:
    """ Serve as a custom route predicate function for ogcproxy.
    We do not want the OGC proxy to be used to reach the app's
    mapserv script. We just return False if the url includes
    "mapserv". It is rather drastic, but works for us. """

    def __init__(self, val, config):
        del val  # unused
        del config  # unused
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
            LOG.info("Unable to get host name for %s: %s", url, e)
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
            (k.lower(), v.lower()) for k, v in request.params.items()
        )
        return "request" not in params or params["request"] != "getcapabilities"

    @staticmethod
    def phash():
        return ""


def add_cors_route(config, pattern, service):
    """
    Add the OPTIONS route and view need for services supporting CORS.
    """
    def view(request):  # pragma: no cover
        from c2cgeoportal_geoportal.lib.caching import set_common_headers, NO_CACHE
        return set_common_headers(request, service, NO_CACHE)

    name = pattern + "_options"
    config.add_route(name, pattern, request_method="OPTIONS")
    config.add_view(view, route_name=name)


def error_handler(http_exception, request):  # pragma: no cover
    """
    View callable for handling all the exceptions that are not already handled.
    """
    LOG.warning("%s returned status code %s", request.url, http_exception.status_code)
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
    function_ = getattr(module, parts[-1])
    function_(*args, **kwargs)


def includeme(config: pyramid.config.Configurator):
    """
    This function returns a Pyramid WSGI application.
    """

    settings = config.get_settings()

    config.include("c2cgeoportal_commons")

    call_hook(settings, "after_settings", settings)

    get_user_from_request = create_get_user_from_request(settings)
    config.add_request_method(get_user_from_request, name="user", property=True)
    config.add_request_method(get_user_from_request, name="get_user")

    # Configure 'locale' dir as the translation dir for c2cgeoportal app
    config.add_translation_dirs("c2cgeoportal_geoportal:locale/")

    config.include('c2cwsgiutils.pyramid.includeme')
    health_check = HealthCheck(config)

    # Initialise DBSessions
    init_dbsessions(settings, config, health_check)

    # Initialize the dbreflection module
    dbreflection.init()

    checker.init(config, health_check)
    check_collector.init(config, health_check)

    # dogpile.cache configuration
    if 'cache' in settings:
        caching.init_region(settings['cache'])
        from c2cgeoportal_commons.models.main import InvalidateCacheEvent

        @zope.event.classhandler.handler(InvalidateCacheEvent)
        def handle(event: InvalidateCacheEvent):  # pylint: disable=unused-variable
            del event
            caching.invalidate_region()

    # Register a tween to get back the cache buster path.
    if 'cache_path' not in config.get_settings():
        config.get_settings()['cache_path'] = ['static']
    config.add_tween("c2cgeoportal_geoportal.lib.cacheversion.CachebusterTween")
    config.add_tween("c2cgeoportal_geoportal.lib.headers.HeadersTween")

    # Bind the mako renderer to other file extensions
    add_mako_renderer(config, ".html")
    add_mako_renderer(config, ".js")

    package = config.get_settings()["package"]

    # Add the "geojson" renderer
    config.add_renderer("geojson", GeoJSON())

    # Add decimal json renderer
    config.add_renderer("decimaljson", DecimalJSON())

    # Add the "xsd" renderer
    config.add_renderer("xsd", XSD(
        include_foreign_keys=True
    ))

    # Add the set_user_validator directive, and set a default user validator
    config.add_directive("set_user_validator", set_user_validator)
    config.set_user_validator(default_user_validator)

    config.add_route('dynamic', '/dynamic.json', request_method="GET")
    if settings.get("ogcproxy_enable", False):  # pragma: no cover
        # Add an OGCProxy view
        config.add_route_predicate("ogc_server", OgcproxyRoutePredicate)
        config.add_route(
            "ogcproxy", "/ogcproxy",
            ogc_server=True
        )
        config.add_view("papyrus_ogcproxy.views:ogcproxy", route_name="ogcproxy")

    # Add routes to the mapserver proxy
    config.add_route_predicate("mapserverproxy", MapserverproxyRoutePredicate)
    config.add_route(
        "mapserverproxy", "/mapserv_proxy",
        mapserverproxy=True, pregenerator=C2CPregenerator(role=True),
    )

    # Add route to the tinyows proxy
    config.add_route(
        "tinyowsproxy", "/tinyows_proxy",
        pregenerator=C2CPregenerator(role=True),
    )

    # Add routes to the entry view class
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

    config.add_renderer(".map", AssetRendererFactory)
    config.add_renderer(".css", AssetRendererFactory)
    config.add_renderer(".ico", AssetRendererFactory)
    config.add_route("apijs", "/api.js", request_method="GET")
    config.add_route("oldxapijs", "/xapi.js", request_method="GET")
    config.add_route("oldapihelp", "/oldapihelp.html", request_method="GET")
    config.add_route("oldxapihelp", "/oldxapihelp.html", request_method="GET")

    # Cannot be at the header to do not load the model too early
    from c2cgeoportal_geoportal.views.entry import Entry

    def add_api_route(name: str, attr: str, path: str, renderer: str):
        config.add_route(name, path, request_method="GET")
        config.add_view(
            Entry, attr=attr, route_name=name,
            renderer='{}_geoportal:static-ngeo/{}'.format(package, renderer)
        )
    add_api_route('favicon', 'favicon', '/favicon.ico', 'js/apps/image/favicon.ico')
    add_api_route('apijsmap', 'apijsmap', '/api.js.map', "build/api.js.map")
    add_api_route('apicss', 'apicss', '/api.css', "build/api.css")
    add_api_route('apihelp', 'apihelp', '/apihelp/index.html', "api/apihelp/index.html")
    c2cgeoportal_geoportal.views.add_redirect(
        config, 'apihelp_redirect', '/apihelp.html', '/apihelp/index.html'
    )

    config.add_route(
        "themes", "/themes",
        request_method="GET",
        pregenerator=C2CPregenerator(role=True),
    )

    config.add_route("invalidate", "/invalidate", request_method="GET")

    # Print proxy routes
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

    # Full-text search routes
    add_cors_route(config, "/search", "fulltextsearch")
    config.add_route("fulltextsearch", "/search")

    # Access to raster data
    add_cors_route(config, "/raster", "raster")
    config.add_route("raster", "/raster", request_method="GET")

    add_cors_route(config, "/profile.{ext}", "profile")
    config.add_route("profile.csv", "/profile.csv", request_method="POST")
    config.add_route("profile.json", "/profile.json", request_method="POST")

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
        request_method="POST", header=GEOJSON_CONTENT_TYPE)
    config.add_route(
        "layers_update", "/layers/{layer_id:\\d+}/{feature_id}",
        request_method="PUT", header=GEOJSON_CONTENT_TYPE)
    config.add_route(
        "layers_delete", "/layers/{layer_id:\\d+}/{feature_id}",
        request_method="DELETE")
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
    add_cors_route(config, "/memory", "memory")
    config.add_route("memory", "/memory", request_method="GET")

    # Scan view decorator for adding routes
    config.scan(ignore=[
        "c2cgeoportal_geoportal.lib",
        "c2cgeoportal_geoportal.scaffolds",
        "c2cgeoportal_geoportal.scripts"
    ])

    if "subdomains" in settings:  # pragma: no cover
        config.registry.registerUtility(
            MultiDomainStaticURLInfo(), IStaticURLInfo)

    add_admin_interface(config)

    # Add the project static view with cache buster
    from c2cgeoportal_geoportal.lib.cacheversion import version_cache_buster
    config.add_static_view(
        name="static",
        path="{}_geoportal:static".format(package),
        cache_max_age=int(config.get_settings()["default_max_age"]),
    )
    config.add_cache_buster("{}_geoportal:static".format(package), version_cache_buster)

    # Add the project static view without cache buster
    config.add_static_view(
        name="static-ngeo",
        path="{}_geoportal:static-ngeo".format(package),
        cache_max_age=int(config.get_settings()["default_max_age"]),
    )

    # Handles the other HTTP errors raised by the views. Without that,
    # the client receives a status=200 without content.
    config.add_view(error_handler, context=HTTPException)

    c2cwsgiutils.index.additional_title = '<div class="row"><div class="col-lg-3"><h2>GeoMapFish</h2>' \
        '</div><div class="col-lg">'
    c2cwsgiutils.index.additional_auth.extend([
        '<a href="../tiles/admin/">TileCloud chain admin</a><br>',
        '<a href="../tiles/c2c/">TileCloud chain c2c tools</a><br>',
        '<a href="../invalidate">Invalidate the cache</a><br>',
        '<a href="../memory">Memory status</a><br>',
    ])
    if config.get_settings().get('enable_admin_interface', False):
        c2cwsgiutils.index.additional_noauth.append('<a href="../admin/">Admin</a><br>')

    c2cwsgiutils.index.additional_noauth.append(
        '</div></div><div class="row"><div class="col-lg-3"><h3>Interfaces</h3></div><div class="col-lg">'
    )
    c2cwsgiutils.index.additional_noauth.append('<a href="../">Default</a><br>')
    for interface in config.get_settings().get("interfaces", []):
        if interface != config.get_settings().get("default_interface"):
            c2cwsgiutils.index.additional_noauth.append(
                '<a href="../{interface}">{interface}</a><br>'.format(
                    interface=interface
                )
            )
    c2cwsgiutils.index.additional_noauth.append('<a href="../apihelp/index.html">API help</a><br>')
    c2cwsgiutils.index.additional_noauth.append('<a href="../oldapihelp.html">Old API help</a><br>')
    c2cwsgiutils.index.additional_noauth.append('<a href="../oldxapihelp.html">Old extended API help</a><br>')
    c2cwsgiutils.index.additional_noauth.append('</div></div><hr>')


def init_dbsessions(settings: dict, config: Configurator, health_check: HealthCheck = None) -> None:
    db_chooser = settings.get('db_chooser', {})
    master_paths = [re.compile(i.replace('//', '/')) for i in db_chooser.get('master', [])]
    slave_paths = [re.compile(i.replace('//', '/')) for i in db_chooser.get('slave', [])]

    slave_prefix = 'sqlalchemy_slave' if 'sqlalchemy_slave.url' in settings else None

    c2cgeoportal_commons.models.DBSession, rw_bind, _ = c2cwsgiutils.db.setup_session(
        config, 'sqlalchemy', slave_prefix, force_master=master_paths, force_slave=slave_paths)
    c2cgeoportal_commons.models.Base.metadata.bind = rw_bind
    c2cgeoportal_commons.models.DBSessions['dbsession'] = c2cgeoportal_commons.models.DBSession

    for dbsession_name, dbsession_config in settings.get('dbsessions', {}).items():  # pragma: nocover
        c2cgeoportal_commons.models.DBSessions[dbsession_name] = \
            c2cwsgiutils.db.create_session(config, dbsession_name, **dbsession_config)

    c2cgeoportal_commons.models.Base.metadata.clear()
    from c2cgeoportal_commons.models import main

    if health_check is not None:
        for name, session in c2cgeoportal_commons.models.DBSessions.items():
            if name == 'dbsession':
                health_check.add_db_session_check(
                    session, at_least_one_model=main.Theme, level=1
                )
                alembic_ini = os.path.join(os.path.abspath(os.path.curdir), 'alembic.ini')
                if os.path.exists(alembic_ini):
                    health_check.add_alembic_check(
                        session, alembic_ini_path=alembic_ini, name='main',
                        version_schema=settings['schema'], level=1
                    )
                    health_check.add_alembic_check(
                        session, alembic_ini_path=alembic_ini, name='static',
                        version_schema=settings['schema_static'], level=1
                    )
            else:  # pragma: no cover
                def check(session_: Session) -> None:
                    session_.execute('SELECT 1')
                health_check.add_db_session_check(session, query_cb=check, level=2)
