# -*- coding: utf-8 -*-

from pyramid.view import view_config

@view_config(route_name='mobile', renderer='sitn:static/mobile/index.html')
@view_config(route_name='mobile_production', renderer='sitn:static/mobile/build/production/index.html')
def mobile(request):
    return {}
