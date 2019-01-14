<%
import json
from sqlalchemy import func
from c2cgeoportal_commons import models
from c2cgeoportal_commons.models import main
from c2cgeoportal_geoportal.lib.cacheversion import get_cache_version

interface_name = request.params.get('interface')
if interface_name not in request.registry.settings.get('interfaces'):
    interface_name = request.registry.settings.get('default_interface')

interface_config = request.registry.settings['interfaces_config'][interface_name]
lang_urls = {
  lang: request.static_url('{package}_geoportal:static-ngeo/build/{lang}.json'.format(
    package=request.registry.settings["package"], lang=lang
  ))
  for lang in request.registry.settings["available_locale_names"]
}
fulltextsearch_groups = [
  group[0] for group in models.DBSession.query(
    func.distinct(main.FullTextSearch.layer_name)
  ).filter(main.FullTextSearch.layer_name.isnot(None)).all()
]
routes = dict(currentInterfaceUrl=interface_name)
routes.update(interface_config['routes'])
fulltextsearch_params = dict(interface=interface_name)
fulltextsearch_params.update(interface_config['fulltextsearch_params'])
tree_params = dict(
  version=2,
  background='background',
  interface=interface_name,
)
tree_params.update(interface_config.get('tree_params', {}))
wfs_permalink = dict(url=request.route_url('mapserverproxy'))
wfs_permalink.update(interface_config.get('wfs_permalink', {}))
%>

(function() {
  var module = angular.module('App${interface_name}');
% for name, value in interface_config['constants'].items():
  module.constant('${name}', ${json.dumps(value) | n})
% endfor
% for constant, route in routes.items():
  module.constant('${constant}', '${request.route_url(route) | n}');
% endfor
% for constant, static_ in interface_config.get('static', {}).items():
  module.constant('${constant}', '${request.static_url(static_)}');
% endfor
  module.constant('cacheVersion', '${get_cache_version()}');
  module.constant('langUrls', ${json.dumps(lang_urls) | n});
% if 'gmfSearchGroups' not in interface_config['constants']:
  module.constant('gmfSearchGroups', ${json.dumps(fulltextsearch_groups) | n});
% endif
  module.constant('gmfTreeUrl', '${request.route_url('themes', _query=tree_params) | n}');
  module.constant('fulltextsearchUrl', '${request.route_url('fulltextsearch', _query=fulltextsearch_params) | n}');
  module.constant('ngeoWfsPermalinkOptions', ${json.dumps(wfs_permalink) | n});

% if 'redirect_interface' in interface_config:
<%
    import urllib.parse
    no_redirect_query = {
        'no_redirect': 't'
    }
    if 'query' in request.params:
        query = urllib.parse.parse_qs(request.params['query'][1:])
        no_redirect_query.update(query)
    else:
        query = {}
    if 'themes' in request.matchdict:
        no_redirect_url = request.route_url(
            interface_config['redirect_interface'] + 'theme',
            themes=request.matchdict['themes'],
            _query=no_redirect_query
        )
        url = request.route_url(
            interface_config['redirect_interface'] + 'theme',
            themes=request.matchdict['themes'],
            _query=query
        )
    else:
        no_redirect_url = request.route_url(
            interface_config['redirect_interface'],
            _query=no_redirect_query
        )
        url = request.route_url(
            interface_config['redirect_interface'],
            _query=query
        )
%>
% if 'no_redirect' in query:
    module.constant('redirectUrl', '');
% else:
% if interface_config.get('do_redirect', False):
    var small_screen = window.matchMedia ? window.matchMedia('(max-width: 1024px)') : false;
    if (small_screen && (('ontouchstart' in window) || window.DocumentTouch && document instanceof DocumentTouch)) {
      window.location = '${url | n}';
    }
% else:
  module.constant('redirectUrl', '${no_redirect_url | n}');
% endif
% endif
% endif

  var gmfAbstractAppControllerModule = angular.module('GmfAbstractAppControllerModule');
  gmfAbstractAppControllerModule.constant('angularLocaleScript', '${request.static_url(request.registry.settings['package'] + '_geoportal:static-ngeo/build/')}angular-locale_{{locale}}.js');
})();
