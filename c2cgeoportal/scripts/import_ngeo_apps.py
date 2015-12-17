# -*- coding: utf-8 -*-

# Copyright (c) 2011-2015, Camptocamp SA
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


import re
from argparse import ArgumentParser


def main():  # pragma: no cover
    """
    Import the ngeo apps files
    """

    parser = ArgumentParser(description='import ngeo apps files')

    parser.add_argument('--html', action="store_true", help="Import the html template")
    parser.add_argument('--js', action="store_true", help="Import the javascript controller")
    parser.add_argument('interface', metavar='INTERFACE', help="The interface we import")
    parser.add_argument('src', metavar='SRC', help="The ngeo source file")
    parser.add_argument('dst', metavar='DST', help="The destination file")

    args = parser.parse_args()

    with open(args.src) as src:
        data = src.read()
        data = re.sub(r"{{", r"\\{\\{", data)
        data = re.sub(r"}}", r"\\}\\}", data)
        data = re.sub("app", "{{package}}", data)

        if args.js:
            # Full text search
            data = re.sub(r"datasetTitle: 'Internal',", r"datasetTitle: '{{project}}',", data)

        if args.html:
            # back for ng-app
            data = re.sub(r"ng-{{package}}", r"ng-app", data)
            # back for mobile-web-app-capable
            data = re.sub(
                r"mobile-web-{{package}}-capable",
                r"mobile-web-app-capable", data
            )
            # Styles
            data = re.sub(
                r'    <link rel="stylesheet.* type="text/css">',
                r"""% if debug:
    <link rel="stylesheet/less" href="${{request.static_url('%s/ngeo/contribs/gmf/less/font.less' % request.registry.settings['node_modules_path'])}}" type="text/css">
    <link rel="stylesheet/less" href="${{request.static_url('{{{{package}}}}:static-ngeo/less/{interface}.less')}}" type="text/css">
    <link rel="stylesheet/less" href="${{request.static_url('%s/ngeo/contribs/gmf/less/{interface}.less' % request.registry.settings['node_modules_path'])}}" type="text/css">
% else:
    <link rel="stylesheet" href="${{request.static_url('{{{{package}}}}:static-ngeo/build/{interface}.css')}}" type="text/css">
% endif""".format(interface=args.interface),  # noqa
                data,
                count=1,
                flags=re.DOTALL
            )
            # Scripts
            data = re.sub(
                r'    <script .*watchwatchers.js"></script>',
                r"""% if debug:
    <script>
        window.CLOSURE_BASE_PATH = '';
        window.CLOSURE_NO_DEPS = true;
    </script>
    <script src="${{request.static_url('%s/jquery/dist/jquery.js' % request.registry.settings['node_modules_path'])}}"></script>
    <script src="${{request.static_url('%s/angular/angular.js' % request.registry.settings['node_modules_path'])}}"></script>
    <script src="${{request.static_url('%s/angular-gettext/dist/angular-gettext.js' % request.registry.settings['node_modules_path'])}}"></script>
    <script src="${{request.static_url('%s/bootstrap/dist/js/bootstrap.js' % request.registry.settings['node_modules_path'])}}"></script>
    <script src="${{request.static_url('%s/proj4/dist/proj4-src.js' % request.registry.settings['node_modules_path'])}}"></script>
    <script src="${{request.static_url('%s/d3/d3.min.js' % request.registry.settings['node_modules_path'])}}"></script>
    <script src="${{request.static_url('%s/typeahead.js/dist/typeahead.bundle.js' % request.registry.settings['node_modules_path'])}}"></script>
    <script src="${{request.static_url('%s/closure/goog/base.js' % request.registry.settings['closure_library_path'])}}"></script>
    <script src="${{request.route_url('deps.js')}}"></script>
    <script>
        goog.require('{{{{package}}}}_{interface}');
    </script>
    <script src="${{request.static_url('{{{{package}}}}:static-ngeo/build/templatecache.js')}}"></script>
    <script src="${{request.static_url('%s/ngeo/utils/watchwatchers.js' % request.registry.settings['closure_library_path'])}}"></script>
    <script src="${{request.static_url('%s/less/dist/less.min.js' % request.registry.settings['node_modules_path'])}}"></script>
% else:
    <script src="${{request.static_url('{{{{package}}}}:static-ngeo/build/{interface}.js')}}"></script>
% endif""".format(interface=args.interface),  # noqa
                data,
                count=1,
                flags=re.DOTALL
            )
            # Full text search
            data = re.sub(
                r"fulltextsearch: 'http://geomapfish-demo.camptocamp.net/2.0/wsgi/fulltextsearch\?query=%QUERY'",  # noqa
                r"fulltextsearch: '${request.route_url('fulltextsearch') | n}?query=%QUERY'",
                data,
            )

        with open(args.dst, "wt") as dst:
            dst.write(data)
