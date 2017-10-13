import os


def includeme(config):
    config.add_static_view('node_modules', 'c2cgeoportal_admin:node_modules/')
    config.override_asset(to_override='c2cgeoportal_admin:node_modules/',
                          override_with=os.path.join(os.path.dirname(__file__),
                                                     '..',
                                                     'node_modules'))

    config.add_static_view('static', 'static', cache_max_age=3600)

    config.add_route('home', '/')
    config.include('c2cgeoform.routes')
