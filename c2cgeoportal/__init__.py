# -*- coding: utf-8 -*-

from pyramid.mako_templating import renderer_factory as mako_renderer_factory
from pyramid.security import unauthenticated_userid
import sqlalchemy
import sqlahelper
import pyramid_tm
import papyrus_ogcproxy

from papyrus.renderers import GeoJSON, XSD

from c2cgeoportal.resources import FAModels
from c2cgeoportal.views.tilecache import load_tilecache_config
from c2cgeoportal.lib import dbreflection

# used by (sql|form)alchemy
srid = None
schema = None
parentschema = None
formalchemy_language = None
formalchemy_default_zoom = 10
formalchemy_default_lon = 740000
formalchemy_default_lat = 5860000
formalchemy_available_functionalities = ""


def locale_negotiator(request):
    """ Our locale negotiator. Returns a locale name or None.
    """
    lang = request.params.get('lang')
    if lang is None:
        lang = request.registry.settings.get("default_language")
        for l in list(request.accept_language):
            if l in request.registry.settings. \
                    get("available_languages").split():
                lang = l
                break
    return lang


def get_user_from_request(request):
    """ Return the User object for the request. Return
    ``None`` if user is anonymous.
    """
    from c2cgeoportal.models import DBSession, User
    username = unauthenticated_userid(request)
    if username is not None:
        return DBSession.query(User).filter_by(
                    username=username).one()


def includeme(config):
    """ This function returns a Pyramid WSGI application.
    """
    global srid
    global schema
    global parentschema
    global formalchemy_language
    global formalchemy_default_zoom
    global formalchemy_default_lon
    global formalchemy_default_lat
    global formalchemy_available_functionalities

    config.set_request_property(
        get_user_from_request, name='user', reify=True)

    # configure 'locale' dir as the translation dir for c2cgeoportal app
    config.add_translation_dirs('c2cgeoportal:locale/')

    # initialize database
    engine = sqlalchemy.engine_from_config(config.get_settings(),
            'sqlalchemy.')
    sqlahelper.add_engine(engine)
    config.include(pyramid_tm.includeme)

    # initialize the dbreflection module
    dbreflection.init(engine)

    # bind the mako renderer to other file extensions
    config.add_renderer('.html', mako_renderer_factory)
    config.add_renderer('.js', mako_renderer_factory)

    # add the "geojson" renderer
    config.add_renderer('geojson', GeoJSON())

    # add the "xsd" renderer
    config.add_renderer('xsd', XSD(
            sequence_callback=dbreflection._xsd_sequence_callback))

    # add a TileCache view
    load_tilecache_config(config.get_settings())
    config.add_route('tilecache', '/tilecache{path:.*?}')
    config.add_view(view='c2cgeoportal.views.tilecache:tilecache',
            route_name='tilecache')

    # add an OGCProxy view
    config.include(papyrus_ogcproxy.includeme)

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
    config.add_route('login', '/login')
    config.add_route('logout', '/logout')
    config.add_route('testi18n', '/testi18n.html')
    config.add_route('apiloader', '/apiloader.js')
    config.add_route('apihelp', '/apihelp.html')
    config.add_route('themes', '/themes')

    # checker routes
    config.add_route('checker_summary', '/checker_summary')
    config.add_route('checker_main', '/checker_main')
    config.add_route('checker_apiloader', '/checker_apiloader')
    config.add_route('checker_printcapabilities', '/checker_printcapabilities')
    config.add_route('checker_pdf', '/checker_pdf')
    config.add_route('checker_fts', '/checker_fts')
    config.add_route('checker_wmscapabilities', '/checker_wmscapabilities')
    config.add_route('checker_wfscapabilities', '/checker_wfscapabilities')

    # print proxy routes
    config.add_route('printproxy', '/printproxy')
    config.add_route('printproxy_info', '/printproxy/info.json')
    config.add_route('printproxy_create', '/printproxy/create.json')
    config.add_route('printproxy_get', '/printproxy/{file}.printout')

    # full text search routes
    config.add_route('fulltextsearch', '/fulltextsearch')

    # add routes for the "layers" web service
    config.add_route('layers_count', '/layers/{layer_id:\\d+}/count',
                     request_method='GET')
    config.add_route('layers_metadata', '/layers/{layer_id:\\d+}/md.xsd',
                     request_method='GET')
    config.add_route('layers_read_many',
                     '/layers/{layer_id:\\d+,?(\\d+,)*\\d*$}',
                     request_method='GET')  # supports URLs like /layers/1,2,3
    config.add_route('layers_read_one', '/layers/{layer_id:\\d+}/{feature_id}',
                     request_method='GET')
    config.add_route('layers_create', '/layers/{layer_id:\\d+}',
                     request_method='POST')
    config.add_route('layers_update', '/layers/{layer_id:\\d+}/{feature_id}',
                     request_method='PUT')
    config.add_route('layers_delete', '/layers/{layer_id:\\d+}/{feature_id}',
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
    formalchemy_default_zoom = \
            config.get_settings()['formalchemy_default_zoom']
    formalchemy_default_lon = config.get_settings()['formalchemy_default_lon']
    formalchemy_default_lat = config.get_settings()['formalchemy_default_lat']
    formalchemy_available_functionalities = \
            config.get_settings()['formalchemy_available_functionalities']

    # register an admin UI
    config.formalchemy_admin('admin', package='c2cgeoportal',
            view='fa.jquery.pyramid.ModelView', factory=FAModels)

    # scan view decorator for adding routes
    config.scan(ignore='c2cgeoportal.tests')

    # add the static view (for static resources)
    config.add_static_view('static', 'c2cgeoportal:static')
