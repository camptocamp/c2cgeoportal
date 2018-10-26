# -*- coding: utf-8 -*-

# Copyright (c) 2011-2018, Camptocamp SA
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
from pyramid.paster import get_app as paster_get_app
from logging.config import fileConfig


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


def get_app(options, parser):
    app_config = options.app_config
    app_name = options.app_name

    if app_name is None and "#" in app_config:
        app_config, app_name = app_config.split("#", 1)
    if not os.path.isfile(app_config):
        parser.error("Cannot find config file: {}".format(app_config))

    # Read the configuration
    env = {
        "VISIBLE_ENTRY_POINT": "cli",
        "LOG_LEVEL": "INFO",
        "C2CGEOPORTAL_LOG_LEVEL": "WARN",
        "GUNICORN_LOG_LEVEL": "INFO",
        "GUNICORN_ACCESS_LOG_LEVEL": "INFO",
        "SQL_LOG_LEVEL": "INFO",
        "OTHER_LOG_LEVEL": "INFO",
        "LOG_HOST": "localhost",
        "LOG_PORT": "0",
    }
    env.update(os.environ)
    fileConfig(app_config, defaults=env)
    return paster_get_app(app_config, options.app_name, options=os.environ)
