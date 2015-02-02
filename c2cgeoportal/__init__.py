# -*- coding: utf-8 -*-

# Copyright (c) 2011-2015, Camptocamp SA
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


import yaml

from pyramid_mako import add_mako_renderer
from pyramid.interfaces import IStaticURLInfo

import sqlalchemy
import sqlahelper
import pyramid_tm

from papyrus.renderers import GeoJSON, XSD
import simplejson as json

from c2cgeoportal.lib import dbreflection, get_setting, caching, \
    MultiDomainPregenerator, MultiDomainStaticURLInfo


# used by (sql|form)alchemy
srid = None
schema = None
parentschema = None
formalchemy_language = None
formalchemy_default_zoom = 10
formalchemy_default_x = 740000
formalchemy_default_y = 5860000
formalchemy_available_functionalities = []
formalchemy_available_metadata = []


class DecimalJSON:
    def __init__(self, jsonp_param_name='callback'):
        self.jsonp_param_name = jsonp_param_name

    def __call__(self, info):
        def _render(value, system):
            ret = json.dumps(value, use_decimal=True)
            request = system.get('request')
            if request is not None:
                callback = request.params.get(self.jsonp_param_name)
                if callback is None:
                    request.response.content_type = 'application/json'
                else:
                    request.response.content_type = 'text/javascript'
                    ret = '%(callback)s(%(json)s);' % {
                        'callback': callback,
                        'json': ret
                    }
            return ret
        return _render

INTERFACE_TYPE_CGXP = 'cgxp'
INTERFACE_TYPE_SENCHA_TOUCH = 'senchatouch'
INTERFACE_TYPE_NGEO = 'ngeo'
INTERFACE_TYPE_NGEO_CATALOGUE = 'ngeo'


def add_interface(
    config, interface_name=None, interface_type=INTERFACE_TYPE_CGXP, **kwargs
):  # pragma: nocover
    if interface_type == INTERFACE_TYPE_CGXP:
        if interface_name is None:
            add_interface_cgxp(
                config,
                interface_name='main',
                route_names=('home', 'viewer'),
                routes=('/', '/viewer.js'),
                renderers=('index.html', 'viewer.js'),
            )
        else:
            add_interface_cgxp(
                config,
                interface_name=interface_name,
                route_names=(interface_name, interface_name + '.js'),
                routes=('/%s' % interface_name, '/%s.js' % interface_name),
                renderers=('/%s.html' % interface_name, '/%s.js' % interface_name),
            )

    elif interface_type == INTERFACE_TYPE_SENCHA_TOUCH:
        add_interface_senchatouch(config, interface_name, **kwargs)

    elif interface_type == INTERFACE_TYPE_NGEO:
        if interface_name is None:
            add_interface_ngeo(
                config,
                interface_name='main',
                route_name='home',
                route='/',
                renderer='index.html',
            )
        else:
            add_interface_ngeo(
                config,
                interface_name=interface_name,
                route_name=interface_name,
                route='/%s' % interface_name,
                renderer='/%s.html' % interface_name,
            )


def add_interface_cgxp(config, interface_name, route_names, routes, renderers):  # pragma: nocover
    # Cannot be at the header to don't load the model too early
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
        attr='get_cgxp_index_vars',
        route_name=route_names[0],
        renderer=renderers[0]
    )
    # permalink theme: recover the theme for generating custom viewer.js url
    config.add_route(
        '%stheme' % route_names[0],
        '%s%stheme/*themes' % (routes[0], '' if routes[0][-1] == '/' else '/')
    )
    config.add_view(
        Entry,
        decorator=add_interface,
        attr='get_cgxp_permalinktheme_vars',
        route_name='%stheme' % route_names[0],
        renderer=renderers[0]
    )
    config.add_route(route_names[1], routes[1])
    config.add_view(
        Entry,
        decorator=add_interface,
        attr='get_cgxp_viewer_vars',
        route_name=route_names[1],
        renderer=renderers[1]
    )


def add_interface_senchatouch(config, interface_name, package=None):  # pragma: nocover
    # Cannot be at the header to don't load the model too early
    from c2cgeoportal.views.entry import Entry

    if package is None:
        package = config.get_settings()['package']

    def add_interface(f):
        def new_f(root, request):
            request.interface_name = interface_name
            return f(root, request)
        return new_f

    interface_name = 'mobile' if interface_name is None else interface_name
    config.add_route('mobile_index_dev', '/mobile_dev/')
    config.add_view(
        Entry,
        decorator=add_interface,
        attr='mobile',
        renderer='%(package)s:static/mobile/index.html' % {
            'package': package
        },
        route_name='mobile_index_dev'
    )
    config.add_route('mobile_config_dev', '/mobile_dev/config.js')
    config.add_view(
        Entry,
        decorator=add_interface,
        attr='mobileconfig',
        renderer='%(package)s:static/mobile/config.js' % {
            'package': package
        },
        route_name='mobile_config_dev'
    )
    config.add_static_view('%s_dev' % interface_name, '%(package)s:static/mobile' % {
        'package': package
    })

    config.add_route('mobile_index_prod', '/mobile/')
    config.add_view(
        Entry,
        decorator=add_interface,
        attr='mobile',
        renderer='%(package)s:static/mobile/build/production/App/index.html' % {
            'package': package
        },
        route_name='mobile_index_prod'
    )
    config.add_route('mobile_config_prod', '/mobile/config.js')
    config.add_view(
        Entry,
        decorator=add_interface,
        attr='mobileconfig',
        renderer='%(package)s:static/mobile/build/production/App/config.js' % {
            'package': package
        },
        route_name='mobile_config_prod'
    )
    config.add_static_view(interface_name, '%(package)s:static/mobile/build/production/App' % {
        'package': package
    })


def add_interface_ngeo(config, interface_name, route_name, route, renderer):  # pragma: nocover
    # Cannot be at the header to don't load the model too early
    from c2cgeoportal.views.entry import Entry

    def add_interface(f):
        def new_f(root, request):
            request.interface_name = interface_name
            return f(root, request)
        return new_f

    config.add_route(route_name, route)
    config.add_view(
        Entry,
        decorator=add_interface,
        attr='get_ngeo_index_vars',
        route_name=route_name,
        renderer=renderer
    )
    # permalink theme: recover the theme for generating custom viewer.js url
    config.add_route(
        '%stheme' % route_name,
        '%s%stheme/*themes' % (route, '' if route[-1] == '/' else '/')
    )
    config.add_view(
        Entry,
        decorator=add_interface,
        attr='get_ngeo_permalinktheme_vars',
        route_name='%stheme' % route_name,
        renderer=renderer
    )


def locale_negotiator(request):
    lang = request.params.get('lang')
    if lang is None:
        # if best_match returns None then Pyramid will use what's defined in
        # the default_locale_name configuration variable
        return request.accept_language.best_match(
            request.registry.settings.get("available_locale_names"))
    return lang


def get_user_from_request(request):
    """ Return the User object for the request.

    Return ``None`` if user is anonymous or if it does not
    exist in the database.
    """
    from c2cgeoportal.models import DBSession, User
    from sqlalchemy.orm import joinedload

    if not hasattr(request, '_user'):
        request._user = None
        username = request.authenticated_userid
        if username is not None:
            # We know we will need the role object of the
            # user so we use joined loading
            request._user = DBSession.query(User) \
                .options(joinedload(User.role)) \
                .filter_by(username=username) \
                .first()

    return request._user


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
    config.action('user_validator', register)


def default_user_validator(request, username, password):
    """ Validate the username/password. This is c2cgeoportal's
    default user validator. """
    from c2cgeoportal.models import DBSession, User
    user = DBSession.query(User).filter_by(username=username).first()
    return username if user and user.validate_password(password) else None


def ogcproxy_route_predicate(info, request):
    """ Serve as a custom route predicate function for ogcproxy.
    We do not want the OGC proxy to be used to reach the app's
    mapserv script. We just return False if the url includes
    "mapserv". It is rather drastic, but works for us. """
    url = request.params.get('url')
    if url is None:
        return False
    if url.find('mapserv') > 0:
        return False
    return True


def mapserverproxy_route_predicate(info, request):
    """ Serve as a custom route predicate function for mapserverproxy.
    If the hide_capabilities setting is set and is true then we want to
    return 404s on GetCapabilities requests."""
    hide_capabilities = request.registry.settings.get('hide_capabilities')
    if not hide_capabilities:
        return True
    params = dict(
        (k.lower(), unicode(v).lower()) for k, v in request.params.iteritems()
    )
    return 'request' not in params or params['request'] != u'getcapabilities'


def includeme(config):
    """ This function returns a Pyramid WSGI application.
    """

    # update the settings object from the YAML application config file
    settings = config.get_settings()
    settings.update(yaml.load(file(settings.get('app.cfg'))))

    global srid
    global schema
    global parentschema
    global formalchemy_language
    global formalchemy_default_zoom
    global formalchemy_default_x
    global formalchemy_default_y
    global formalchemy_available_functionalities
    global formalchemy_available_metadata

    config.set_request_property(get_user_from_request, name='user')

    # configure 'locale' dir as the translation dir for c2cgeoportal app
    config.add_translation_dirs('c2cgeoportal:locale/')

    # initialize database
    engine = sqlalchemy.engine_from_config(
        config.get_settings(),
        'sqlalchemy.')
    sqlahelper.add_engine(engine)
    config.include(pyramid_tm.includeme)

    # initialize the dbreflection module
    dbreflection.init(engine)

    # dogpile.cache configuration
    caching.init_region(settings['cache'])
    caching.invalidate_region()

    # bind the mako renderer to other file extensions
    add_mako_renderer(config, '.html')
    add_mako_renderer(config, '.js')
    config.include('pyramid_chameleon')

    # add the "geojson" renderer
    config.add_renderer('geojson', GeoJSON())

    # add decimal json renderer
    config.add_renderer('decimaljson', DecimalJSON())

    # add the "xsd" renderer
    config.add_renderer('xsd', XSD(
        sequence_callback=dbreflection._xsd_sequence_callback))

    # add the set_user_validator directive, and set a default user
    # validator
    config.add_directive('set_user_validator', set_user_validator)
    config.set_user_validator(default_user_validator)

    # add an OGCProxy view
    config.add_route(
        'ogcproxy', '/ogcproxy',
        custom_predicates=(ogcproxy_route_predicate,))
    config.add_view('papyrus_ogcproxy.views:ogcproxy', route_name='ogcproxy')

    # add routes to the mapserver proxy
    config.add_route(
        'mapserverproxy', '/mapserv_proxy',
        custom_predicates=(mapserverproxy_route_predicate,),
        pregenerator=MultiDomainPregenerator())

    # add routes to csv view
    config.add_route('csvecho', '/csv')

    # add routes to the echo service
    config.add_route('echo', '/echo')

    # add routes to the entry view class
    config.add_route('loginform', '/login.html')
    config.add_route('login', '/login')
    config.add_route('logout', '/logout')
    config.add_route('loginchange', '/loginchange')
    config.add_route('testi18n', '/testi18n.html')
    config.add_route('apijs', '/api.js')
    config.add_route('xapijs', '/xapi.js')
    config.add_route('apihelp', '/apihelp.html')
    config.add_route('xapihelp', '/xapihelp.html')
    config.add_route('themes', '/themes')
    config.add_route('invalidate', '/invalidate')

    # checker routes, Checkers are web services to test and assess that
    # the application is correctly functioning.
    # These web services are used by tools like (nagios).
    config.add_route('checker_main', '/checker_main')
    config.add_route('checker_viewer', '/checker_viewer')
    config.add_route('checker_edit', '/checker_edit')
    config.add_route('checker_edit_js', '/checker_edit_js')
    config.add_route('checker_api', '/checker_api')
    config.add_route('checker_xapi', '/checker_xapi')
    config.add_route('checker_printcapabilities', '/checker_printcapabilities')
    config.add_route('checker_pdf', '/checker_pdf')
    config.add_route('checker_fts', '/checker_fts')
    config.add_route('checker_wmscapabilities', '/checker_wmscapabilities')
    config.add_route('checker_wfscapabilities', '/checker_wfscapabilities')
    # collector
    config.add_route('check_collector', '/check_collector')

    # print proxy routes
    config.add_route('printproxy', '/printproxy')
    config.add_route('printproxy_info', '/printproxy/info.json')
    config.add_route('printproxy_create', '/printproxy/create.json')
    config.add_route('printproxy_get', '/printproxy/{file}.printout')

    # full text search routes
    config.add_route('fulltextsearch', '/fulltextsearch')

    # Access to raster data
    config.add_route('raster', '/raster')
    config.add_route('profile.csv', '/profile.csv')
    config.add_route('profile.json', '/profile.json')

    # shortener
    config.add_route('shortener_create', '/short/create')
    config.add_route('shortener_get', '/short/{ref}')

    # add routes for the "layers" web service
    config.add_route(
        'layers_count', '/layers/{layer_id:\\d+}/count',
        request_method='GET')
    config.add_route(
        'layers_metadata', '/layers/{layer_id:\\d+}/md.xsd',
        request_method='GET')
    config.add_route(
        'layers_read_many',
        '/layers/{layer_id:\\d+,?(\\d+,)*\\d*$}',
        request_method='GET')  # supports URLs like /layers/1,2,3
    config.add_route(
        'layers_read_one', '/layers/{layer_id:\\d+}/{feature_id}',
        request_method='GET')
    config.add_route(
        'layers_create', '/layers/{layer_id:\\d+}',
        request_method='POST')
    config.add_route(
        'layers_update', '/layers/{layer_id:\\d+}/{feature_id}',
        request_method='PUT')
    config.add_route(
        'layers_delete', '/layers/{layer_id:\\d+}/{feature_id}',
        request_method='DELETE')
    config.add_route(
        'layers_enumerate_attribute_values',
        '/layers/{layer_name}/values/{field_name}',
        request_method='GET')
    # there's no view corresponding to that route, it is to be used from
    # mako templates to get the root of the "layers" web service
    config.add_route('layers_root', '/layers/')

    # pyramid_formalchemy's configuration
    config.include('pyramid_formalchemy')
    config.include('fa.jquery')

    # define the srid, schema and parentschema
    # as global variables to be usable in the model
    srid = config.get_settings()['srid']
    schema = config.get_settings()['schema']
    parentschema = config.get_settings()['parentschema']
    settings = config.get_settings()
    formalchemy_default_zoom = get_setting(
        settings,
        ('admin_interface', 'map_zoom'), formalchemy_default_zoom)
    formalchemy_default_x = get_setting(
        settings,
        ('admin_interface', 'map_x'), formalchemy_default_x)
    formalchemy_default_y = get_setting(
        settings,
        ('admin_interface', 'map_y'), formalchemy_default_y)
    formalchemy_available_functionalities = get_setting(
        settings,
        ('admin_interface', 'available_functionalities'),
        formalchemy_available_functionalities)
    formalchemy_available_metadata = get_setting(
        settings,
        ('admin_interface', 'available_metadata'),
        formalchemy_available_metadata)

    # scan view decorator for adding routes
    config.scan(ignore='c2cgeoportal.tests')

    config.registry.registerUtility(
        MultiDomainStaticURLInfo(), IStaticURLInfo)
    # add the static view (for static resources)
    config.add_static_view(
        'static', 'c2cgeoportal:static',
        cache_max_age=int(settings["default_max_age"])
    )
