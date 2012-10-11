# -*- coding: utf-8 -*-

import yaml

from pyramid.mako_templating import renderer_factory as mako_renderer_factory
from pyramid.security import unauthenticated_userid

import sqlalchemy
import sqlahelper
import pyramid_tm

from papyrus.renderers import GeoJSON, XSD
import simplejson as json

from c2cgeoportal.resources import FAModels
from c2cgeoportal.views.tilecache import load_tilecache_config
from c2cgeoportal.lib import dbreflection, get_setting, caching

# used by (sql|form)alchemy
srid = None
schema = None
parentschema = None
formalchemy_language = None
formalchemy_default_zoom = 10
formalchemy_default_x = 740000
formalchemy_default_y = 5860000
formalchemy_available_functionalities = []


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


def locale_negotiator(request):
    lang = request.params.get('lang')
    if lang is None:
        # if best_match returns None then Pyramid will use what's defined in
        # the default_locale_name configuration variable
        return request.accept_language.best_match(
            request.registry.settings.get("available_locale_names"))
    return lang


def get_user_from_request(request):
    """ Return the User object for the request. Return
    ``None`` if user is anonymous.
    """
    from c2cgeoportal.models import DBSession, User
    from sqlalchemy.orm import joinedload
    username = unauthenticated_userid(request)
    if username is not None:
        # we know we'll need to role object for the
        # user so we use earger loading
        return DBSession.query(User) \
            .options(joinedload(User.role)) \
            .filter_by(username=username) \
            .one()


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

    config.set_request_property(
        get_user_from_request, name='user', reify=True)

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

    # bind the mako renderer to other file extensions
    config.add_renderer('.html', mako_renderer_factory)
    config.add_renderer('.js', mako_renderer_factory)

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

    # add a TileCache view
    load_tilecache_config(config.get_settings())
    config.add_route('tilecache', '/tilecache{path:.*?}')
    config.add_view(
        view='c2cgeoportal.views.tilecache:tilecache',
        route_name='tilecache')

    # add an OGCProxy view
    config.add_route('ogcproxy', '/ogcproxy',
                     custom_predicates=(ogcproxy_route_predicate,))
    config.add_view('papyrus_ogcproxy.views:ogcproxy', route_name='ogcproxy')

    # add routes to the mapserver proxy
    config.add_route('mapserverproxy', '/mapserv_proxy')

    # add routes to csv view
    config.add_route('csvecho', '/csv')

    # add routes to the echo service
    config.add_route('echo', '/echo')

    # add routes to the entry view class
    config.add_route('home', '/')
    config.add_route('viewer', '/viewer.js')
    config.add_route('edit', '/edit')
    config.add_route('edit.js', '/edit.js')
    config.add_route('loginform', '/login.html')
    config.add_route('login', '/login')
    config.add_route('logout', '/logout')
    config.add_route('testi18n', '/testi18n.html')
    config.add_route('apiloader', '/apiloader.js')
    config.add_route('apihelp', '/apihelp.html')
    config.add_route('themes', '/themes')
    # permalink theme: recover the theme for generating custom viewer.js url
    config.add_route('permalinktheme', '/theme/*themes')

    # checker routes, Checkers are web services to test and assess that
    # the application is correctly functioning.
    # These web services are used by tools like (nagios).
    config.add_route('checker_main', '/checker_main')
    config.add_route('checker_viewer', '/checker_viewer')
    config.add_route('checker_edit', '/checker_edit')
    config.add_route('checker_edit_js', '/checker_edit_js')
    config.add_route('checker_apiloader', '/checker_apiloader')
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

    # register an admin UI
    config.formalchemy_admin(
        'admin', package='c2cgeoportal',
        view='fa.jquery.pyramid.ModelView', factory=FAModels)

    # scan view decorator for adding routes
    config.scan(ignore='c2cgeoportal.tests')

    # add the static view (for static resources)
    config.add_static_view('static', 'c2cgeoportal:static')
