# -*- coding: utf-8 -*-
"""
Copyright: (C) 2020 by Camptocamp SA
Contact: info@camptocamp.com

.. note:: This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by the
    Free Software Foundation; either version 2 of the License, or (at your
    option) any later version.
"""

import logging
from logging.config import fileConfig
import os

from qgis.core import Qgis, QgsMessageLog


def init():
    fileConfig(os.environ.get("LOGGING_CONFIG_FILE", "/var/www/logging.ini"), defaults=dict(os.environ))


class LogHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        # To be visible in the CI
        print(self.format(record))

        QgsMessageLog.logMessage(self.format(record), record.name, level=Qgis.Critical)
