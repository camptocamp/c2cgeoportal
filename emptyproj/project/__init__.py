# -*- coding: utf-8 -*-
from pyramid.config import Configurator
from project.resources import Root

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(root_factory=Root, settings=settings)

    config.include(c2cgeoporal)

    config.add_translation_dirs('project:locale/')

    # scan view decorator for adding routes
    config.scan()

    # add the static view (for static resources)
    config.add_static_view('proj', 'project:static')

    return config.make_wsgi_app()
