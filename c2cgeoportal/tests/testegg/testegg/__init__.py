# -*- coding: utf-8 -*-

# Copyright (c) 2012-2013 by Camptocamp SA


def main(global_config, **settings):
    config.include('c2cgeoportal')

    # scan view decorator for adding routes
    config.scan()

    return config.make_wsgi_app()
