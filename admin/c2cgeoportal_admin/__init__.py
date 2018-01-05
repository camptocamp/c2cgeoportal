from pyramid.config import Configurator
from c2cwsgiutils.health_check import HealthCheck
import c2c.template
import c2cgeoportal_admin.routes

import c2cgeoform
from pkg_resources import resource_filename
search_paths = ((resource_filename(__name__, 'templates/widgets'),) +
                c2cgeoform.default_search_paths)
c2cgeoform.default_search_paths = search_paths


def main(_, **settings):
    """
    This function returns a Pyramid WSGI application.
    """
    settings.update(c2c.template.get_config(settings.get('app.cfg')))

    config = Configurator(settings=settings)
    config.include('c2cwsgiutils.pyramid.includeme')
    config.include('pyramid_jinja2')
    config.include('c2cgeoform')
    config.include('c2cgeoportal_commons')
    config.include(c2cgeoportal_admin.routes)
    config.scan()

    health_check = HealthCheck(config)
    health_check.add_url_check('http://{}/'.format(settings['healthcheck_host']))
    # health_check.add_alembic_check(models.DBSession, '/app/alembic.ini', 1)

    return config.make_wsgi_app()
