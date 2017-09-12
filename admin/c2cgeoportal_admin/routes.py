def includeme(config):
    config.include('c2cgeoform.routes')
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('home', '/')
