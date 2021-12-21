# Copyright (c) 2016-2021, Camptocamp SA
# All rights reserved.

# This program is free software; you can redistribute it and/or modify it under the terms of the
# GNU General Public License as published by the Free Software Foundation; either version 2 of
# the License, or (at your option) any later version.

import logging
import sys
import traceback
from typing import Optional

import qgis.server
from qgis.core import Qgis, QgsMessageLog

from . import gmf_logging

LOG = logging.getLogger(__name__)


def serverClassFactory(  # noqa: ignore=N806
    serverIface: qgis.server.QgsServerInterface,  # noqa: ignore=N803
) -> Optional[qgis.server.QgsAccessControlFilter]:
    LOG.info("Configure logging...")

    try:
        gmf_logging.init(serverIface)
    except Exception:  # pylint: disable=broad-except
        print("".join(traceback.format_exception(*sys.exc_info())))
        QgsMessageLog.logMessage(
            "".join(traceback.format_exception(*sys.exc_info())),
            "GeoMapFishAccessControl",
            level=Qgis.Critical,
        )

    LOG.info("Starting GeoMapFish filter plugin...")

    try:
        from .filter import GeoMapFishFilter  # pylint: disable=import-outside-toplevel

        serverIface.registerFilter(GeoMapFishFilter(serverIface), 100)
    except Exception:  # pylint: disable=broad-except
        LOG.exception("Cannot setup filter plugin")

    LOG.info("Starting GeoMapFish access restriction...")

    try:
        from .accesscontrol import (  # pylint: disable=import-outside-toplevel
            GeoMapFishAccessControl,
            GMFException,
        )

        return GeoMapFishAccessControl(serverIface)
    except GMFException:
        LOG.exception(
            "Cannot setup GeoMapFishAccessControl",
        )
