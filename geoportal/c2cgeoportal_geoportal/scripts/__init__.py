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
from plaster.uri import parse_uri
from pyramid.paster import get_app as paster_get_app, get_appsettings as paster_get_appsettings
from pyramid.scripts.common import get_config_loader
import transaction
from c2c.template.config import config as configuration
from c2cgeoportal_commons.testing import (
    get_engine, get_session_factory, get_tm_session, generate_mappers)


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


def get_app_config(options, parser):
    app_config = options.app_config
    if not os.path.isfile(app_config):
        parser.error("Cannot find config file: {}".format(uri.path))
    return app_config


def get_app_name(options):
    app_config = options.app_config
    app_name = options.app_name
    if app_name is None and "#" in app_config:
        app_config, app_name = app_config.split("#", 1)
    return app_name


def get_defaults():
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
    return env


def get_appsettings(options, parser):
    app_config = get_app_config(options, parser)
    app_name = get_app_name(options)
    defaults = get_defaults()

    loader = get_config_loader(app_config)
    loader.setup_logging(defaults=defaults)
    settings = loader.get_wsgi_app_settings(app_name, defaults=defaults)

    # update the settings object from the YAML application config file
    configuration.init(settings.get('app.cfg'))
    settings.update(configuration.get_config())

    return settings


def get_app(options, parser):
    app_config = get_app_config(options, parser)
    app_name = get_app_name(options)
    defaults = get_defaults()

    loader = get_config_loader(app_config)
    loader.setup_logging(defaults=defaults)
    return loader.get_wsgi_app(app_name, options=defaults)


def get_session(settings):
    generate_mappers()
    engine = get_engine(settings)
    session_factory = get_session_factory(engine)
    session = get_tm_session(session_factory, transaction.manager)
    return session
