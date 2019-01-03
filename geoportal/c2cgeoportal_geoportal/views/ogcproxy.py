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

import logging
from typing import Dict  # noqa, pylint: disable=unused-import

from sqlalchemy.orm.exc import NoResultFound
from c2cgeoportal_geoportal.lib import get_url2
from c2cgeoportal_geoportal.views.proxy import Proxy
from c2cgeoportal_commons.models import DBSession
from c2cgeoportal_commons.models.main import OGCServer
from c2cgeoportal_geoportal.lib.caching import get_region

cache_region = get_region()
log = logging.getLogger(__name__)


class OGCProxy(Proxy):

    params = {}  # type: Dict[str, str]

    def __init__(self, request):
        Proxy.__init__(self, request)

        self.mapserver_settings = request.registry.settings.get("mapserverproxy", {})
        if "default_ogc_server" in self.mapserver_settings:
            self.default_ogc_server = self.get_ogcserver_byname(
                self.mapserver_settings["default_ogc_server"]
            )

        if "external_ogc_server" in self.mapserver_settings:
            self.external_ogc_server = self.get_ogcserver_byname(
                self.mapserver_settings["external_ogc_server"]
            )

        # params hold the parameters we"re going to send to backend
        self.params = dict(self.request.params)

        # reset possible value of role_id and user_id
        if "role_id" in self.params:  # pragma: no cover
            del self.params["role_id"]
        if "user_id" in self.params:  # pragma: no cover
            del self.params["user_id"]

        self.lower_params = self._get_lower_params(self.params)
        self.ogc_server = self.get_ogcserver_byname(self.params["ogcserver"]) \
            if "ogcserver" in self.params else None
        self.external = bool(self.request.params.get("EXTERNAL"))

    @cache_region.cache_on_arguments()
    def get_ogcserver_byname(self, name):
        try:
            result = DBSession.query(OGCServer).filter(OGCServer.name == name).one()
            DBSession.expunge(result)
            return result
        except NoResultFound:  # pragma nocover
            log.error(
                "OGSServer '%s' does not exists (existing: %s).",
                name,
                ",".join([t[0] for t in DBSession.query(OGCServer.name).all()])
            )
            raise

    def _get_ogc_server(self):
        return self.ogc_server or (
            self.external_ogc_server if self.external else self.default_ogc_server
        )

    def _get_wms_url(self):
        ogc_server = self._get_ogc_server()
        errors = set()
        url = get_url2("The OGC server '{}'".format(ogc_server.name), ogc_server.url, self.request, errors)
        if len(errors) > 0:  # pragma: no cover
            log.error("\n".join(errors))
        return url

    def _get_wfs_url(self):
        ogc_server = self._get_ogc_server()
        errors = set()
        url = get_url2(
            "The OGC server (WFS) '{}'".format(ogc_server.name),
            ogc_server.url_wfs or ogc_server.url, self.request, errors
        )
        if len(errors) > 0:  # pragma: no cover
            log.error("\n".join(errors))
        return url
