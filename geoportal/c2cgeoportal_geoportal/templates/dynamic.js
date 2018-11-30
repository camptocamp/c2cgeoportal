<%
import json
%>
(function() {
  var module = angular.module('App${interface_name}');
% for name, value in constants.items():
  module.constant('${name}', ${json.dumps(value) | n})
% endfor

% if do_redirect:
  var small_screen = window.matchMedia ? window.matchMedia('(max-width: 1024px)') : false;
  if (small_screen && (('ontouchstart' in window) || window.DocumentTouch && document instanceof DocumentTouch)) {
    window.location = '${redirect_url | n}';
  }
% endif

  var gmfAbstractAppControllerModule = angular.module('GmfAbstractAppControllerModule');
% for name, value in other_constants.items():
  gmfAbstractAppControllerModule.constant('${name}', ${json.dumps(value) | n})
% endfor
})();
