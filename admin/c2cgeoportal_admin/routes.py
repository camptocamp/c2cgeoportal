def includeme(config):
    config.include('c2cgeoform.routes')
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('home', '/')
    config.add_route('user_', 'user_')
    config.add_route('role_', 'role_')
