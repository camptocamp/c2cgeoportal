## -*- coding: utf-8 -*-
<%doc>
    This is a Mako template that generates Angular code putting the contents of
    HTML partials into Angular's $templateCache. The generated code is then built
    with the rest of JavaScript code. The generated script is not used at all in
    development mode, where HTML partials are loaded through Ajax.
</%doc>
<%
  import re
  import os
  _partials = {}
  for partial in partials.split(' '):
      f = file(partial)
      content = unicode(f.read().decode('utf8'))
      content = re.sub(r'>\s*<' , '><', content)
      content = re.sub(r'\s\s+', ' ', content)
      content = re.sub(r'\n', '', content)
      content = re.sub(r"'", "\\'", content)
      dirname, filename = os.path.split(partial)
      subdirname = os.path.basename(dirname.rstrip(os.sep))
      _partials[os.path.join(subdirname, filename)] = content
%>\
/**
 * @fileoverview Directive templates cache.
 *
 * GENERATED FILE. DO NOT EDIT.
 */

goog.require('app');

(function() {
  /**
   * @param {angular.$cacheFactory.Cache} $templateCache
   * @ngInject
   */
  var runner = function($templateCache) {
  % for partial in _partials:
    $templateCache.put('${partial}', '${_partials[partial]}');
  %endfor
  };

  app.module.run(runner);
})();\
