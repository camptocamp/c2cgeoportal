from pyramid.config import Configurator


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(settings=settings)
    config.include('pyramid_jinja2')

    '''
    import c2cgeoportal_models
    c2cgeoportal_models.schema = 'main'
    c2cgeoportal_models.srid = 3847
    '''

    config.include('c2cgeoportal_models')
    config.include('.routes')
    config.scan()
    return config.make_wsgi_app()
