# Copyright (c) 2021, Camptocamp SA
# All rights reserved.

# This program is free software; you can redistribute it and/or modify it under the terms of the
# GNU General Public License as published by the Free Software Foundation; either version 2 of
# the License, or (at your option) any later version.

# This plugin is used to correctly set the HTTP headers

import logging

from qgis.server import QgsServerFilter

LOG = logging.getLogger(__name__)


class GeoMapFishFilter(QgsServerFilter):
    # def __init__(self, server_iface):
    #    super().__init__(server_iface)
    #    self.server_iface = server_iface

    def responseComplete(self):
        LOG.error("@@@@@@@@@@@@@@@@@@@@@@@@@@ responseComplete")
        LOG.error(self.serverInterface().requestHandler().requestHeaders())

    def sendResponse(self):
        LOG.error("@@@@@@@@@@@@@@@@@@@@@@@@@@ sendResponse")
        LOG.error(self.serverInterface().requestHandler().requestHeaders())

    def requestReady(self):
        LOG.error("@@@@@@@@@@@@@@@@@@@@@@@@@@ requestReady")
        LOG.error(self.serverInterface().getEnv("HTTP_X_QGIS_SERVICE_URL"))

        self.serverInterface().requestHandler().setRequestHeader(
            "X-Qgis-Service-Url", self.serverInterface().getEnv("HTTP_X_QGIS_SERVICE_URL")
        )
        LOG.error(self.serverInterface().requestHandler().requestHeaders())
