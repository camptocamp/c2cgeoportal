from translationstring import TranslationStringFactory
from pyramid.config import Configurator
from c2cwsgiutils.health_check import HealthCheck
from pyramid.events import BeforeRender, NewRequest

import c2cgeoform
from pkg_resources import resource_filename

from c2c.template.config import config as configuration
from c2cgeoportal_admin.subscribers import add_renderer_globals, add_localizer


search_paths = (
    (resource_filename(__name__, 'templates/widgets'),) +
    c2cgeoform.default_search_paths
)
c2cgeoform.default_search_paths = search_paths

_ = TranslationStringFactory('c2cgeoportal_admin')


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

    session_factory = get_session_factory(get_engine(settings))
    config.registry['dbsession_factory'] = session_factory

    # Make request.dbsession available for use in Pyramid
    config.add_request_method(
        # request.tm is the transaction manager used by pyramid_tm
        lambda request: get_tm_session(session_factory, request.tm),
        'dbsession',
        reify=True
    )

    config.add_subscriber(add_renderer_globals, BeforeRender)
    config.add_subscriber(add_localizer, NewRequest)

    generate_mappers()

    health_check = HealthCheck(config)
    health_check.add_url_check('http://{}/'.format(settings['healthcheck_host']))

    return config.make_wsgi_app()


class PermissionSetter:

    def __init__(self, config):
        self.default_permission_to_revert = None
        self.config = config

    def __enter__(self):
        self.config.commit()  # avoid .ConfigurationConflictError
        if self.config.introspector.get_category('default permission'):
            self.default_permission_to_revert = \
                self.config.introspector.get_category('default permission')[0]['introspectable']['value']
        self.config.set_default_permission('admin')

    def __exit__(self, _type, value, traceback):
        self.config.commit()  # avoid .ConfigurationConflictError
        self.config.set_default_permission(self.default_permission_to_revert)


def includeme(config: Configurator):
    config.include('pyramid_jinja2')
    config.include('c2cgeoform')
    config.include('c2cgeoportal_commons')
    config.include('c2cgeoportal_admin.routes')
    # Use pyramid_tm to hook the transaction lifecycle to the request
    config.include('pyramid_tm')
    config.add_translation_dirs('c2cgeoportal_admin:locale')

    with PermissionSetter(config):
        config.scan()
