from pyramid.config import Configurator
from pyramid.mako_templating import renderer_factory as mako_renderer_factory
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid_formalchemy.resources import Models
import sqlalchemy
import sqlahelper
import pyramid_tm
import papyrus
import papyrus_ogcproxy

from papyrus.renderers import GeoJSON

from c2cgeoportail.resources import Root
from c2cgeoportail.views.tilecache import load_tilecache_config

# used by (sql|form)alchemy
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
        for l in request.accept_language.best_matches():
            if l in request.registry.settings.get("available_languages").split():
                lang = l
                break
    return lang


def includeme(config):
    """ This function returns a Pyramid WSGI application.
    """
    global schema
    global parentschema
    global formalchemy_language
    global formalchemy_default_zoom
    global formalchemy_default_lon
    global formalchemy_default_lat
    global formalchemy_available_functionalities

    # configure 'locale' dir as the translation dir for c2cgeoportail app
    config.add_translation_dirs('c2cgeoportail:locale/')

    # initialize database
    engine = sqlalchemy.engine_from_config(config.get_settings(), 'sqlalchemy.')
    sqlahelper.add_engine(engine)
    config.include(pyramid_tm.includeme)

    # bind the mako renderer to other file extensions
    config.add_renderer('.html', mako_renderer_factory)
    config.add_renderer('.js', mako_renderer_factory)

    # add the "geojson" renderer
    config.add_renderer('geojson', GeoJSON())

    # add a TileCache view
    load_tilecache_config(config.get_settings())
    config.add_route('tilecache', '/tilecache{path:.*?}')
    config.add_view(view='c2cgeoportail.views.tilecache:tilecache', route_name='tilecache')

    # add an OGCProxy view
    config.include(papyrus_ogcproxy.includeme)

    # add routes to the mapserver proxy
    config.add_route('mapserverproxy', '/mapserv_proxy')

    # add routes to csv view
    config.add_route('csvecho', '/csv')

    # add routes to the entry view class
    config.add_route('home', '/')
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
    config.add_route('printproxy_get', '/printproxy/{id}.pdf.printout')

    # full text search routes
    config.add_route('fulltextsearch', '/fulltextsearch')

    # add routes for MapFish web services
    config.include(papyrus.includeme)

    # pyramid_formalchemy's configuration
    config.include('pyramid_formalchemy')
    config.include('fa.jquery')

    # define the schema as a global variavle to be usable in the model
    schema = config.get_settings()['schema']
    parentschema = config.get_settings()['parentschema']
    formalchemy_default_zoom = config.get_settings()['formalchemy_default_zoom']
    formalchemy_default_lon = config.get_settings()['formalchemy_default_lon']
    formalchemy_default_lat = config.get_settings()['formalchemy_default_lat']
    formalchemy_available_functionalities = config.get_settings()['formalchemy_available_functionalities']

    config.override_asset( 
            to_override="fa.jquery:templates/admin/", 
            override_with="c2cgeoportail:templates/admin/") 
 
    # register an admin UI 
    config.formalchemy_model('/admin/functionality', package='c2cgeoportail', 
            view='fa.jquery.pyramid.ModelView', model='c2cgeoportail.models.Functionality')
    config.formalchemy_model('/admin/theme', package='c2cgeoportail', 
            view='fa.jquery.pyramid.ModelView', model='c2cgeoportail.models.Theme')
    config.formalchemy_model('/admin/layer', package='c2cgeoportail', 
            view='fa.jquery.pyramid.ModelView', model='c2cgeoportail.models.Layer')
    config.formalchemy_model('/admin/layergroup', package='c2cgeoportail', 
            view='fa.jquery.pyramid.ModelView', model='c2cgeoportail.models.LayerGroup')
    config.formalchemy_model('/admin/restrictionarea', package='c2cgeoportail', 
            view='fa.jquery.pyramid.ModelView', model='c2cgeoportail.models.RestrictionArea')
    config.formalchemy_model('/admin/role', package='c2cgeoportail', 
            view='fa.jquery.pyramid.ModelView', model='c2cgeoportail.models.Role')
    config.formalchemy_model('/admin/user', package='c2cgeoportail', 
            view='fa.jquery.pyramid.ModelView', model='c2cgeoportail.models.User')
    config.add_route('admin', '/admin')

    config.formalchemy_admin('administration', package='c2cgeoportail', factory=Models)

    # scan view decorator for adding routes
    config.scan()

    # add the static view (for static resources)
    config.add_static_view('static', 'c2cgeoportail:static')

