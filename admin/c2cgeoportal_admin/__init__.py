from translationstring import TranslationStringFactory
from pyramid.config import Configurator
from c2cwsgiutils.health_check import HealthCheck

import c2cgeoform
from pkg_resources import resource_filename

from c2cgeoportal_commons.config import config as configuration

search_paths = (
    (resource_filename(__name__, 'templates/widgets'),) +
    c2cgeoform.default_search_paths
)
c2cgeoform.default_search_paths = search_paths

_ = TranslationStringFactory('admin')


def main(_, **settings):
    """
    This function returns a Pyramid WSGI application.
    """
    configuration.init(settings.get('app.cfg'))
    settings.update(configuration.get_config())

    config = Configurator(settings=settings)
    config.include('c2cwsgiutils.pyramid.includeme')

    config.include('c2cgeoportal_admin')

    from c2cgeoportal_commons.testing import (
        generate_mappers,
        get_engine,
        get_session_factory,
        get_tm_session,
    )

    # Initialize the dev dbsession
    settings = config.get_settings()
    settings['tm.manager_hook'] = 'pyramid_tm.explicit_manager'

    # use pyramid_tm to hook the transaction lifecycle to the request
    config.include('pyramid_tm')

    session_factory = get_session_factory(get_engine(settings))
    config.registry['dbsession_factory'] = session_factory

    # make request.dbsession available for use in Pyramid
    config.add_request_method(
        # r.tm is the transaction manager used by pyramid_tm
        lambda r: get_tm_session(session_factory, r.tm),
        'dbsession',
        reify=True
    )

    generate_mappers()

    health_check = HealthCheck(config)
    health_check.add_url_check('http://{}/'.format(settings['healthcheck_host']))

    return config.make_wsgi_app()


def includeme(config: Configurator):
    config.include('pyramid_jinja2')
    config.include('c2cgeoform')
    config.include('c2cgeoportal_commons')
    config.include('c2cgeoportal_admin.routes')
    # use pyramid_tm to hook the transaction lifecycle to the request
    config.include('pyramid_tm')
    config.scan()
