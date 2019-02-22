# -*- coding: utf-8 -*-

# Copyright (c) 2011-2019, Camptocamp SA
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
from urllib.parse import urlsplit, urlunsplit
from pyramid.scripts.common import get_config_loader


def fill_arguments(parser):
    default_app_config = "geoportal/production.ini" \
        if os.path.isfile("geoportal/production.ini") \
        else "production.ini"

    parser.add_argument(
        "--app-config", "-i",
        default=default_app_config,
        help="The application .ini config file (optional, default is '{}')".format(default_app_config)
    )
    parser.add_argument(
        "--app-name", "-n",
        default="app",
        help="The application name (optional, default is 'app')"
    )


def get_config_uri(options):
    uri = urlsplit(options.app_config)
    return urlunsplit((
        uri.scheme or 'c2cgeoportal',
        uri.netloc,
        uri.path,
        uri.query,
        options.app_name or uri.fragment
    ))


def get_appsettings(options, defaults=None):
    config_uri = get_config_uri(options)
    loader = get_config_loader(config_uri)
    loader.setup_logging()
    return loader.get_wsgi_app_settings(defaults=defaults)
