# -*- coding: utf-8 -*-


def main(global_config, **settings):
    config.include('c2cgeoportal')

    # scan view decorator for adding routes
    config.scan()

    return config.make_wsgi_app()
