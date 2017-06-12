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

import logging

from sqlalchemy.orm.exc import NoResultFound
from c2cgeoportal.views.proxy import Proxy
from c2cgeoportal.models import DBSession, OGCServer
from c2cgeoportal.lib.caching import get_region

cache_region = get_region()
log = logging.getLogger(__name__)


class OGCProxy(Proxy):

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

    @cache_region.cache_on_arguments()
    def get_ogcserver_byname(self, name):
        try:
            result = DBSession.query(OGCServer).filter(OGCServer.name == name).one()
            DBSession.expunge(result)
            return result
        except NoResultFound:  # pragma nocover
            log.error("OGSServer '{}' does not exists (existing: {}).".format(
                name, ",".join([t[0] for t in DBSession.query(OGCServer.name).all()])))
            raise
