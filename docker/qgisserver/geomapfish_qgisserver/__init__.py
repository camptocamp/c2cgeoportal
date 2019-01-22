# -*- coding: utf-8 -*-
"""
Copyright: (C) 2016 by Camptocamp SA
Contact: info@camptocamp.com

.. note:: This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by the
    Free Software Foundation; either version 2 of the License, or (at your
    option) any later version.
"""


from qgis.core import QgsMessageLog
from geomapfish_qgisserver.accesscontrol import GMFException


def serverClassFactory(serverIface):  # noqa
    QgsMessageLog.logMessage("Starting GeoMapFish access restriction...")

    try:
        from geomapfish_qgisserver.accesscontrol import GeoMapFishAccessControl
        return GeoMapFishAccessControl(serverIface)
    except GMFException as e:
        QgsMessageLog.logMessage(str(e))
