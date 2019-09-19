from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config

from c2cgeoportal_geoportal.lib.cacheversion import get_cache_version
from c2cgeoportal_geoportal.lib.caching import NO_CACHE, set_common_headers


@view_config(route_name='localejson')
def locale(request):
    response = HTTPFound(
        request.static_url(
            '{package}_geoportal:static-ngeo/build/{lang}.json'.format(
                package=request.registry.settings["package"],
                lang=request.locale_name
            ),
            _query={
                'cache': get_cache_version(),
            }
        )
    )
    set_common_headers(request, 'api', NO_CACHE, response=response)
    return response
