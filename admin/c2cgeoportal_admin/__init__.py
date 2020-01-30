# -*- coding: utf-8 -*-

# Copyright (c) 2017-2020, Camptocamp SA
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


from c2c.template.config import config as configuration
import c2cgeoform
import c2cwsgiutils.pretty_json
from pkg_resources import resource_filename
from pyramid.config import Configurator
from pyramid.events import BeforeRender, NewRequest
from sqlalchemy import engine_from_config
from sqlalchemy.orm import configure_mappers, sessionmaker
from translationstring import TranslationStringFactory
import zope.sqlalchemy

from c2cgeoportal_admin.subscribers import add_localizer, add_renderer_globals

search_paths = (resource_filename(__name__, "templates/widgets"),) + c2cgeoform.default_search_paths
c2cgeoform.default_search_paths = search_paths

_ = TranslationStringFactory("c2cgeoportal_admin")


def main(_, **settings):
    """
    This function returns a Pyramid WSGI application.
    """
    configuration.init(settings.get("app.cfg"))
    settings.update(configuration.get_config())

    config = Configurator(settings=settings)

    c2cwsgiutils.pretty_json.init(config)
    config.include("c2cgeoportal_admin")

    # Initialize the dev dbsession
    settings = config.get_settings()
    settings["tm.manager_hook"] = "pyramid_tm.explicit_manager"

    configure_mappers()
    engine = engine_from_config(settings)
    session_factory = sessionmaker()
    session_factory.configure(bind=engine)

    def get_tm_session(session_factory, transaction_manager):
        dbsession = session_factory()
        zope.sqlalchemy.register(dbsession, transaction_manager=transaction_manager)
        return dbsession

    # Make request.dbsession available for use in Pyramid
    config.add_request_method(
        # request.tm is the transaction manager used by pyramid_tm
        lambda request: get_tm_session(session_factory, request.tm),
        "dbsession",
        reify=True,
    )

    config.add_subscriber(add_renderer_globals, BeforeRender)
    config.add_subscriber(add_localizer, NewRequest)

    return config.make_wsgi_app()


class PermissionSetter:
    def __init__(self, config):
        self.default_permission_to_revert = None
        self.config = config

    def __enter__(self) -> None:
        self.config.commit()  # avoid .ConfigurationConflictError
        if self.config.introspector.get_category("default permission"):
            self.default_permission_to_revert = self.config.introspector.get_category("default permission")[
                0
            ]["introspectable"]["value"]
        self.config.set_default_permission("admin")

    def __exit__(self, _type, value, traceback):
        self.config.commit()  # avoid .ConfigurationConflictError
        self.config.set_default_permission(self.default_permission_to_revert)


def includeme(config: Configurator):
    config.include("pyramid_jinja2")
    config.include("c2cgeoform")
    config.include("c2cgeoportal_commons")
    config.include("c2cgeoportal_admin.routes")
    # Use pyramid_tm to hook the transaction lifecycle to the request
    config.include("pyramid_tm")
    config.add_translation_dirs("c2cgeoportal_admin:locale")

    with PermissionSetter(config):
        config.scan()
