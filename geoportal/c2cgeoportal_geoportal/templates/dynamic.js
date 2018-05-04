<%
from json import dumps
from c2cgeoportal.lib.cacheversion import get_cache_version
interface_name = request.params['interface']
interface_config = request.registry.settings['interfaces_config'][interface_name]
lang_urls = {
  lang: request.static_url('epfl_authgeoportail:static-ngeo/build/{lang}.json'.format(lang=lang))
  for lang in request.registry.settings["available_locale_names"]
}
simple_routes = map(currentInterfaceUrl=interface_name)
simple_routes.update(interface_config['routes'])
fulltextsearch_params = map(interface=interface_name)
fulltextsearch_params.update(interface_config['fulltextsearch_params'])
tree_params = map(
  version=2,
  background='background',
  interface=interface_name,
)
tree_params.update(interface_config.get('tree_params', {})
wfs_permalink = map(url=request.route_url('mapservproxy'))
wfs_permalink.update(interface_config.get('wfs_permalink', {})
%>

(function() {
  var module = angular.module('App' + ${the_interface[0].upper() + the_interface[1:]});
%for name, value in interface_config['constants'].items():
  module.constant('${name}', ${json.dump(value)})
%endfor
  module.constant('langUrls', ${json.dump(lang_urls) | n});
  module.constant('cacheVersion', '${get_cache_version()}');
  module.constant('ngeoWfsPermalinkOptions', ${json.dump(wfs_permalink)});
%for constant, route in simple_routes.items():
  module.constant('${constant}', '${request.route_url(${route}) | n}');
%endfor
  module.constant('gmfTreeUrl', '${request.route_url('themes', _query=tree_params) | n}');
  module.constant('fulltextsearchUrl', '${request.route_url('search', _query=fulltextsearch_params) | n}');
%for constant, static_ in interface_config.get('static', {}).items():
  module.constant('${constant}', '${request.static_url('${static_}')}');
%endfor
  module.constant('ngeoWfsPermalinkOptions', ${json.dumps(wfs_permalink)});

  var gmfAbstractAppControllerModule = angular.module('GmfAbstractAppControllerModule');
  gmfAbstractAppControllerModule.constant('angularLocaleScript', '${ request.static_url(request.registry.settings['project'] + ':static-ngeo/build/') }angular-locale_{{locale}}.js');
})();
