# -*- coding: utf-8 -*-

# Copyright (c) 2011-2017, Camptocamp SA
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# The views and conclusions contained in the software and documentation are those
# of the authors and should not be interpreted as representing official policies,
# either expressed or implied, of the FreeBSD Project.


import os
import re
import subprocess
from json import loads, dumps
from urlparse import parse_qsl
from argparse import ArgumentParser


def _sub(pattern, repl, string, count=0, flags=0, required=True):
    new_string = re.sub(pattern, repl, string, count=count, flags=flags)
    if required and new_string == string:
        print("Unable to find the pattern:")
        print(pattern)
        print("in")
        print(string)
        exit(1)
    return new_string


def _subs(subs, string):
    for pattern, repl in subs:
        if repl is False:
            if re.search(pattern, string) is not None:
                return string
        else:
            new_string = re.sub(pattern, repl, string)
            if new_string != string:
                return new_string
    print("Unable to find the patterns:")
    print("\n".join([p for p, r in subs]))
    print("in")
    print(string)
    exit(1)


class _RouteDest:

    def __init__(self, constant, route):
        self.constant = constant
        self.route = route

    def __call__(self, matches):
        query_string = matches.group(1)
        query = ''
        if len(query_string) > 0:
            query = ", _query={0!s}".format(dumps(dict(parse_qsl(query_string))))
        return r"module.constant('{0!s}', '${{request.route_url('{1!s}'{2!s}) | n}}');".format(
            self.constant, self.route, query
        )


RE_NPM_VERSION = re.compile("^([0-9]+)\.([0-9]+)\.([0-9]+)$")
RE_NPM_PRERELEASE_VERSION = re.compile("^([0-9]+)\.([0-9]+)\.([0-9]+)\.?([a-z]+)([0-9]+)$")


def _ngeo_version():
    if "TRAVIS_TAG" in os.environ and os.environ["TRAVIS_TAG"] != "":
        match = RE_NPM_VERSION.match(os.environ["TRAVIS_TAG"])
        prerelease_match = RE_NPM_PRERELEASE_VERSION.match(os.environ["TRAVIS_TAG"])
        if match is not None:
            return "{}.{}.{}".format(match.group(1), match.group(2), match.group(3))
        if prerelease_match is not None:
            return "{}.{}.{}-{}.{}".format(
                prerelease_match.group(1),
                prerelease_match.group(2),
                prerelease_match.group(3),
                prerelease_match.group(4),
                prerelease_match.group(5)
            )
    return None


def _ngeo_git_version():
    version = _ngeo_version()
    if version is not None:
        return version
    if "TRAVIS_TAG" in os.environ and os.environ["TRAVIS_TAG"] != "":
        return os.environ["TRAVIS_TAG"]
    return "master"


def ngeo_git_version():
    print(_ngeo_git_version())


def _get_ngeo_version():
    version = _ngeo_version()
    if version is not None:
        return version
    return "git://github.com/camptocamp/ngeo#{}".format(
        subprocess.check_output(["git", "rev-parse", "HEAD"], cwd="ngeo").strip()
    )


def main():
    """
    Import the ngeo apps files
    """

    parser = ArgumentParser(description='import ngeo apps files')

    parser.add_argument('--html', action="store_true", help="Import the html template")
    parser.add_argument('--js', action="store_true", help="Import the javascript controller")
    parser.add_argument('--package', action="store_true", help="Import the package JSON")
    parser.add_argument('interface', metavar='INTERFACE', help="The interface we import")
    parser.add_argument('src', metavar='SRC', help="The ngeo source file")
    parser.add_argument('dst', metavar='DST', help="The destination file")

    args = parser.parse_args()

    with open(args.src) as src:
        data = src.read()

        if args.package:
            ngeo_json_data = loads(data)
            json_data = {}
            json_data["name"] = "{{package}}"
            json_data["version"] = "2.0.0"
            json_data["description"] = "A GeoMapFish project"

            json_data["devDependencies"] = ngeo_json_data["devDependencies"]
            # freeze the ngeo version
            json_data["devDependencies"]["ngeo"] = _get_ngeo_version()
            for package in [
                "angular-jsdoc",
                "angular-mocks",
                "coveralls",
                "gaze",
                "jsdoc",
                "jsdom",
                "karma",
                "karma-coverage",
                "karma-jasmine",
                "karma-chrome-launcher",
            ]:
                if package in json_data["devDependencies"]:
                    del json_data["devDependencies"][package]

            data = dumps(json_data, indent=2, sort_keys=True, encoding="utf-8", separators=(',', ': '))
            data = data + "\n"

        else:
            data = re.sub(r"{{", r"\\{\\{", data)
            data = re.sub(r"}}", r"\\}\\}", data)

            if args.html:
                if args.interface == "mobile":
                    data = _sub(
                        r"</head>",
                        """</head>
  <%
    no_redirect_query = dict(request.GET)
    no_redirect_query['no_redirect'] = u''
  %>
    """,
                        data,
                    )
                    data = _sub(
                        re.escape(
                            r"http://camptocamp.github.io/ngeo/master/"
                            r"examples/contribs/gmf/apps/desktop/?no_redirect"
                        ),
                        "${request.route_url('desktop', _query=no_redirect_query) | n}",
                        data,
                    )
                if args.interface == "desktop":
                    data = _sub(
                        r"<head>",
                        """<head>
    % if "no_redirect" not in request.params:
            <script>
                if (('ontouchstart' in window) || window.DocumentTouch && document instanceof DocumentTouch) {
                    window.location = "${request.route_url('mobile', _query=dict(request.GET)) | n}";
                }
            </script>
    % endif
    """,
                        data,
                    )

            data = re.sub("app", "{{package}}", data)
            data = re.sub(re.escape("{{package}}lication"), "application", data)
            data = re.sub(re.escape("{{package}}le"), "apple", data)

# temporary disable ...
#        if args.js:
            # Full text search
#            data = _sub(r"datasetTitle: 'Internal',", r"datasetTitle: '{{project}}',", data)

        if args.html:
            data = "<%\n" \
                "from json import dumps\n" \
                "from c2cgeoportal.lib.cacheversion import get_cache_version\n" \
                "%>\n" + \
                data
            # back for ng-app
            data = _sub(r"ng-{{package}}", r"ng-app", data)
            # back for gmf-app- css prefix
            data = _sub(r"gmf-{{package}}-", r"gmf-app-", data, required=False)
            if args.interface == "mobile":
                # back for mobile-web-app-capable
                data = _sub(
                    r"mobile-web-{{package}}-capable",
                    r"mobile-web-app-capable", data
                )
            else:
                data = _sub(
                    r'<img src="image/([^"]+)"( alt="")? ?/>',
                    '<img src="${request.static_url(\'{{package}}:static-ngeo/images/\\1\')}" />',
                    data,
                )
            data = _sub(
                r'<link rel="shortcut icon" href="image/favicon.ico"/>',
                '<link rel="shortcut icon" href="${request.static_url(\'{{package}}:static-ngeo/images/favicon.ico\')}"/>',  # noqa
                data,
            )
            # Styles
            data = _sub(
                r'    <link rel="stylesheet.*/build/{}.css">'.format(args.interface),
                r"""    <link rel="stylesheet" href="${{request.static_url('{{{{package}}}}:static-ngeo/build/{interface}.css')}}" type="text/css">""".format(interface=args.interface),  # noqa
                data,
                count=1,
                flags=re.DOTALL
            )
            # Scripts
            data = _sub(
                "({})".format(re.escape(r'<script src="../../../../')),
                r"""% if debug:
    <script>
        window.CLOSURE_BASE_PATH = '';
        window.CLOSURE_NO_DEPS = true;
    </script>
    \1""",
                data, count=1
            )
            data = _sub(
                re.escape('    <script src="/@?main=') + ".*" + re.escape('watchwatchers.js"></script>'),
                r"""
    <script src="${{request.static_url('%s/closure/goog/base.js' % request.registry.settings['closure_library_path'])}}"></script>
    <script src="${{request.route_url('deps.js')}}"></script>
    <script>
        goog.require('{{{{package}}}}_{interface}');
    </script>
    <script src="${{request.static_url('{{{{package}}}}:static-ngeo/build/templatecache.js')}}"></script>
    <script src="${{request.static_url('%s/ngeo/utils/watchwatchers.js' % request.registry.settings['node_modules_path'])}}"></script>
    <script>
        {{{{package}}}}.componentsBaseTemplateUrl = '${{request.static_url("{{{{package}}}}:static-ngeo/components")}}';
        // {{{{package}}}}.partialsBaseTemplateUrl = '${{request.static_url("{{{{package}}}}:static-ngeo/partials")}}';
        // {{{{package}}}}.baseTemplateUrl = '${{request.static_url("{{{{package}}}}:static-ngeo/js")}}';
    </script>
% else:
    <script src="${{request.static_url('{{{{package}}}}:static-ngeo/build/{interface}.js')}}"></script>
% endif""".format(interface=args.interface),  # noqa
                data,
                count=1,
                flags=re.DOTALL
            )
            data = _sub(
                '{}([^"]+){}(.*){}'.format(
                    re.escape('<script src="../../../../node_modules/'),
                    re.escape('"'),
                    re.escape("></script>"),
                ),
                r"""<script src="${request.static_url('%s/\1' % request.registry.settings['node_modules_path'])}"\2></script>""",  # noqa
                data,
            )
            data = _sub(
                '{}([^"]+){}(.*){}'.format(
                    re.escape('<script src="../../../../'),
                    re.escape('"'),
                    re.escape("></script>"),
                ),
                r"""<script src="${request.static_url('%s/ngeo/\1' % request.registry.settings['node_modules_path'])}"\2></script>""",  # noqa
                data,
            )
            # i18n
            data = _sub(
                "module.constant\('defaultLang', 'en'\);",
                "module.constant('defaultLang', "
                "'${request.registry.settings[\"default_locale_name\"]}');",
                data,
            )
            data = _sub(re.escape(r"""
        var cacheVersion = '0';
"""), "", data)
            data = _sub(
                re.escape(r"""
        var angularLocaleScriptUrlElements = urlElements.slice(0, urlElements.length - 3);
        angularLocaleScriptUrlElements.push('build', 'angular-locale_\{\{locale\}\}.js?cache_version=' + cacheVersion);"""),  # noqa
                "",
                data,
            )
            data = _sub(
                re.escape(
                    "gmfModule.constant('angularLocaleScript', "
                    "angularLocaleScriptUrlElements.join('/'));"
                ),
                "gmfModule.constant('angularLocaleScript', "
                "'${request.static_url('{{package}}:static-ngeo/build/')}"
                "angular-locale_\{\{locale\}\}.js');",
                data,
            )
            data = _sub(
                re.escape("""
        var langUrls = {};
        ['en', 'fr', 'de'].forEach(function(lang) {
            var langUrlElements = urlElements.slice(0, urlElements.length - 3);
            langUrlElements.push('build', 'gmf-' + lang + '.json?cache_version=' + cacheVersion)
            langUrls[lang] = langUrlElements.join('/')
        });"""),
                r"""        var langUrls = {
${ ',\\n'.join([
    "          '{lang}': '{url}'".format(
        lang=lang,
        url=request.static_url('{{package}}:static-ngeo/build/{lang}.json'.format(lang=lang))
    )
    for lang in request.registry.settings["available_locale_names"]
]) | n}
        };""",
                data,
            )
            data = _sub(
                re.escape("module.constant('cacheVersion', cacheVersion);"),
                "module.constant('cacheVersion', '${get_cache_version()}');",
                data,
            )
            data = _subs(
                [(
                    "module.constant\('gmfSearchGroups', \[\]\);",
                    False
                ), (
                    "module.constant\('gmfSearchGroups', \[[^\]]*\]\);",
                    "module.constant('gmfSearchGroups', ${dumps(fulltextsearch_groups) | n});",
                )],
                data,
            )

            # replace routes
            for constant, url_end, route, required in [
                ("authenticationBaseUrl", r"", "base", True),
                ("fulltextsearchUrl", r"/fulltextsearch", "fulltextsearch", True),
                ("gmfRasterUrl", r"/raster", "raster", args.interface != "mobile"),
                ("gmfProfileJsonUrl", r"/profile.json", "profile.json", args.interface != "mobile"),
                ("gmfPrintUrl", r"/printproxy", "printproxy", args.interface != "mobile"),
                ("gmfTreeUrl", r"/themes", "themes", True),
                ("gmfShortenerCreateUrl", r"/short/create", "shortener_create", args.interface != "mobile"),
                ("gmfLayersUrl", r"/layers", "layers_root", args.interface != "mobile"),
            ]:
                data = _sub(
                    r"module.constant\('%s', "
                    "'https://geomapfish-demo.camptocamp.net/2.[0-9]/wsgi%s\??([^\']*)'\);" % (
                        constant, url_end
                    ),
                    _RouteDest(constant, route),
                    data,
                    required=required,
                )
            data = _sub(
                re.escape("module.constant('gmfContextualdatacontentTemplateUrl', window.location.pathname + 'contextualdata.html');"),  # noqa
                "module.constant('gmfContextualdatacontentTemplateUrl', {{package}}.componentsBaseTemplateUrl + '/contextualdata/contextualdata.html');",  # noqa
                data, required=False
            )
            data = _sub(
                re.escape("module.value('ngeoWfsPermalinkOptions',") + ".*defaultFeatureNS",
                """module.value('ngeoWfsPermalinkOptions', /** @type {ngeox.WfsPermalinkOptions} */ ({
              url: '${request.route_url('mapserverproxy') | n}',
              wfsTypes: ${dumps(wfs_types) | n},
              defaultFeatureNS""",
                data,
                count=1,
                flags=re.DOTALL,
            )

        with open(args.dst, "wt") as dst:
            dst.write(data)
