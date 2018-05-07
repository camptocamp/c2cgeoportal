<%
import json
from c2cgeoportal_geoportal.lib.cacheversion import get_cache_version
interface_name = request.params['interface']
interface_config = request.registry.settings['interfaces_config'][interface_name]
lang_urls = {
  lang: request.static_url('{package}_geoportal:static-ngeo/build/{lang}.json'.format(
    package=request.registry.settings["package"], lang=lang
  ))
  for lang in request.registry.settings["available_locale_names"]
}
simple_routes = dict(currentInterfaceUrl=interface_name)
simple_routes.update(interface_config['routes'])
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
  var module = angular.module('App' + ${interface});
%for name, value in interface_config['constants'].items():
  module.constant('${name}', ${json.dumps(value) | n})
%endfor
  module.constant('langUrls', ${json.dumps(lang_urls) | n});
  module.constant('cacheVersion', '${get_cache_version()}');
  module.constant('ngeoWfsPermalinkOptions', ${json.dumps(wfs_permalink) | n});
%for constant, route in simple_routes.items():
  module.constant('${constant}', '${request.route_url(route) | n}');
%endfor
  module.constant('gmfTreeUrl', '${request.route_url('themes', _query=tree_params) | n}');
  module.constant('fulltextsearchUrl', '${request.route_url('fulltextsearch', _query=fulltextsearch_params) | n}');
%for constant, static_ in interface_config.get('static', {}).items():
  module.constant('${constant}', '${request.static_url(static_)}');
%endfor
  module.constant('ngeoWfsPermalinkOptions', ${json.dumps(wfs_permalink) | n});

  var gmfAbstractAppControllerModule = angular.module('GmfAbstractAppControllerModule');
  gmfAbstractAppControllerModule.constant('angularLocaleScript', '${request.static_url(request.registry.settings['package'] + '_geoportal:static-ngeo/build/')}angular-locale_{{locale}}.js');
})();
