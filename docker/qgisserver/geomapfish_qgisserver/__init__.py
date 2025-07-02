# Copyright (c) 2016-2025, Camptocamp SA
# All rights reserved.

# This program is free software; you can redistribute it and/or modify it under the terms of the
# GNU General Public License as published by the Free Software Foundation; either version 2 of
# the License, or (at your option) any later version.

import logging
import sys
import traceback

import qgis.server
from qgis.core import Qgis, QgsMessageLog

from . import gmf_logging

_LOG = logging.getLogger(__name__)


def serverClassFactory(  # noqa: N802 # pylint: disable=invalid-name
    serverIface: qgis.server.QgsServerInterface,  # noqa: N803 # pylint: disable=invalid-name
) -> qgis.server.QgsAccessControlFilter | None:
    """Create a new instance of the access control filter."""
    QgsMessageLog.logMessage("Configure logging...", "GeoMapFish-init", level=Qgis.Info)

    try:
        gmf_logging.init(serverIface)
    except Exception:  # noqa: BLE001 # pylint: disable=broad-except
        QgsMessageLog.logMessage(
            "".join(traceback.format_exception(*sys.exc_info())),
            "GeoMapFish-init",
            level=Qgis.Critical,
        )

    _LOG.info("Starting GeoMapFish access restriction...")

    try:
        from .accesscontrol import (  # noqa: PLC0415 # pylint: disable=import-outside-toplevel
            GeoMapFishAccessControl,
        )

        return GeoMapFishAccessControl(serverIface)
    except Exception:  # noqa: BLE001 # pylint: disable=broad-exception-caught
        _LOG.error("Cannot setup GeoMapFishAccessControl", exc_info=True)
        return None
