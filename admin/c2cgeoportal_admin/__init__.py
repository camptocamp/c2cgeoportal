from pyramid.config import Configurator

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(settings=settings)
    config.include('pyramid_jinja2')
    config.include('c2cgeoform')
    config.include('c2cgeoportal_commons.models')
    config.include('.routes')
    config.scan()
    return config.make_wsgi_app()
