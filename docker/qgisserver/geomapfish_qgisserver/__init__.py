# -*- coding: utf-8 -*-

# Copyright (c) 2016-2020, Camptocamp SA
# All rights reserved.

# This program is free software; you can redistribute it and/or modify it under the terms of the
# GNU General Public License as published by the Free Software Foundation; either version 2 of
# the License, or (at your option) any later version.

import logging
import sys
import traceback

from qgis.core import Qgis, QgsMessageLog

from . import gmf_logging

LOG = logging.getLogger(__name__)


try:
    gmf_logging.init()
except Exception:  # pylint: disable=broad-except
    print("".join(traceback.format_exception(*sys.exc_info())))
    QgsMessageLog.logMessage(
        "".join(traceback.format_exception(*sys.exc_info())),
        "GeoMapFishAccessControl",
        level=Qgis.Critical,
    )


def serverClassFactory(serverIface):  # noqa
    LOG.info("Starting GeoMapFish access restriction...")

    try:
        from .accesscontrol import (  # pylint: disable=import-outside-toplevel
            GeoMapFishAccessControl,
            GMFException,
        )

        return GeoMapFishAccessControl(serverIface)
    except GMFException:
        LOG.error("Cannot setup GeoMapFishAccessControl", exc_info=True)
