# Copyright (c) 2019-2024, Camptocamp SA
# All rights reserved.

# This program is free software; you can redistribute it and/or modify it under the terms of the
# GNU General Public License as published by the Free Software Foundation; either version 2 of
# the License, or (at your option) any later version.

import logging.config
import os
from typing import Any, TextIO

import c2cwsgiutils.pyramid_logging
import qgis.server
from qgis.core import Qgis, QgsMessageLog

SERVER_IFACE: qgis.server.QgsServerInterface = None


def init(server_iface: qgis.server.QgsServerInterface) -> None:
    """Initialize the plugin."""
    global SERVER_IFACE  # pylint: disable=global-statement
    SERVER_IFACE = server_iface
    logging.config.fileConfig(
        os.environ.get("LOGGING_CONFIG_FILE", "/var/www/logging.ini"),
        defaults=dict(os.environ),
    )


class LogHandler(logging.Handler):
    """Python logging handle for QGIS."""

    def emit(self, record: logging.LogRecord) -> None:
        """Emit the record."""
        # To be visible in the CI
        print(self.format(record))

        QgsMessageLog.logMessage(self.format(record), record.name, level=Qgis.Critical)


class _RequestFilter(logging.Filter):
    """A logging filter that adds request information to CEE logs."""

    def filter(self, record: Any) -> bool:
        request_handler = SERVER_IFACE.requestHandler() if SERVER_IFACE else None

        if SERVER_IFACE is not None and request_handler is not None:
            record.path = request_handler.path()
            record.url = request_handler.url()

            id_headers = ["X-Request-ID", "X-Correlation-ID", "Request-ID", "X-Varnish", "X-Amzn-Trace-Id"]
            if "C2C_REQUEST_ID_HEADER" in os.environ:
                id_headers.insert(0, os.environ["C2C_REQUEST_ID_HEADER"])
            for id_header in id_headers:
                env_name = "HTTP_" + id_header.replace("-", "_")
                header = SERVER_IFACE.getEnv(env_name)
                if header:
                    record.request_id = header
                    break

        # record.level_name = record.levelname
        return True


_REQUEST_FILTER = _RequestFilter()


class JsonLogHandler(c2cwsgiutils.pyramid_logging.JsonLogHandler):
    """Log to stdout in JSON."""

    def __init__(self, stream: TextIO | None) -> None:
        """Initialize the handler."""
        super().__init__(stream)
        self.addFilter(_REQUEST_FILTER)

    def emit(self, record: logging.LogRecord) -> None:
        """Emit the record."""
        QgsMessageLog.logMessage(self.format(record), record.name, level=Qgis.Critical)
