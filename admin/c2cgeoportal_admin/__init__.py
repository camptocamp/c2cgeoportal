import c2cwsgiutils.pyramid
from pyramid.config import Configurator
from c2cwsgiutils.health_check import HealthCheck


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(settings=settings)
    config.include('c2cwsgiutils.pyramid.includeme')
    config.include('pyramid_jinja2')

    config.include('c2cgeoportal_commons.models')
    config.include('.routes')
    config.scan()

    health_check = HealthCheck(config)
    #~ health_check.add_db_session_check(models.DBSession, at_least_one_model=models.Hello)
    #~ health_check.add_url_check('http://localhost/api/hello')
    #~ health_check.add_alembic_check(models.DBSession, '/app/alembic.ini', 1)

    return config.make_wsgi_app()
