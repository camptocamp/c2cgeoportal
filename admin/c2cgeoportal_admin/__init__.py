# Copyright (c) 2017-2024, Camptocamp SA
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


from typing import Any

import c2cgeoform
import c2cwsgiutils.pretty_json
import sqlalchemy.orm.session
import zope.sqlalchemy
from c2c.template.config import config as configuration
from pkg_resources import resource_filename
from pyramid.config import Configurator
from pyramid.events import BeforeRender, NewRequest
from sqlalchemy import engine_from_config
from sqlalchemy.orm import configure_mappers, sessionmaker
from transaction import TransactionManager
from translationstring import TranslationStringFactory

from c2cgeoportal_admin.subscribers import add_localizer, add_renderer_globals
from c2cgeoportal_admin.views import IsAdminPredicate

search_paths = (resource_filename(__name__, "templates/widgets"),) + c2cgeoform.default_search_paths
c2cgeoform.default_search_paths = search_paths

_ = TranslationStringFactory("c2cgeoportal_admin")


def main(_, **settings):
    """Return a Pyramid WSGI application."""
    app_cfg = settings.get("app.cfg")
    assert app_cfg is not None
    configuration.init(app_cfg)
    conf = configuration.get_config()
    assert conf is not None
    settings.update(conf)

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

    def get_tm_session(
        session_factory: sessionmaker[  # pylint: disable=unsubscriptable-object
            sqlalchemy.orm.session.Session
        ],
        transaction_manager: TransactionManager,
    ) -> sqlalchemy.orm.session.Session:
        dbsession = session_factory()
        assert isinstance(dbsession, sqlalchemy.orm.session.Session)
        zope.sqlalchemy.register(dbsession, transaction_manager=transaction_manager)
        return dbsession

    # Make request.dbsession available for use in Pyramid
    config.add_request_method(
        # request.tm is the transaction manager used by pyramid_tm
        lambda request: get_tm_session(session_factory, request.tm),
        "dbsession",
        reify=True,
    )

    # Add fake user as we do not have authentication from geoportal
    from c2cgeoportal_commons.models.static import User  # pylint: disable=import-outside-toplevel

    config.add_request_method(
        lambda request: User(
            username="test_user",
        ),
        name="user",
        property=True,
    )

    config.add_route("ogc_server_clear_cache", "/admin/ogc_server_clear_cache/{id}")

    config.add_subscriber(add_renderer_globals, BeforeRender)
    config.add_subscriber(add_localizer, NewRequest)

    return config.make_wsgi_app()


class PermissionSetter:
    """Set the permission to the admin user."""

    def __init__(self, config: Configurator):
        self.default_permission_to_revert = None
        self.config = config

    def __enter__(self) -> None:
        self.config.commit()  # avoid .ConfigurationConflictError
        if self.config.introspector.get_category("default permission"):
            self.default_permission_to_revert = self.config.introspector.get_category("default permission")[
                0
            ]["introspectable"]["value"]
        self.config.set_default_permission("admin")

    def __exit__(self, _type: Any, value: Any, traceback: Any) -> None:
        self.config.commit()  # avoid .ConfigurationConflictError
        self.config.set_default_permission(self.default_permission_to_revert)


def includeme(config: Configurator) -> None:
    """Initialize the Pyramid application."""
    config.include("pyramid_jinja2")
    config.include("c2cgeoform")
    config.include("c2cgeoportal_commons")
    config.include("c2cgeoportal_admin.routes")
    # Use pyramid_tm to hook the transaction lifecycle to the request
    config.include("pyramid_tm")
    config.add_translation_dirs("c2cgeoportal_admin:locale")
    config.add_view_predicate("is_admin", IsAdminPredicate)

    configure_mappers()

    with PermissionSetter(config):
        config.scan()
