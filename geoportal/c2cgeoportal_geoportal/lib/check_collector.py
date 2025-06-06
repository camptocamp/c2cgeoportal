# Copyright (c) 2011-2025, Camptocamp SA
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
from typing import Any, cast

import c2cwsgiutils.health_check
import pyramid.config
import pyramid.request
import requests

from c2cgeoportal_geoportal.lib.checker import build_url

_LOG = logging.getLogger(__name__)


def init(config: pyramid.config.Configurator, health_check: c2cwsgiutils.health_check.HealthCheck) -> None:
    """
    Initialize the check collector.

    Add him in the c2cwsgichecks.
    """
    global_settings = config.get_settings()
    if "check_collector" not in global_settings:
        return
    settings = global_settings["check_collector"]
    c2c_base = global_settings.get("c2c.base_path", "")

    max_level = settings["max_level"]

    for host in settings["hosts"]:

        class Check:
            def __init__(self, host: dict[str, Any]) -> None:
                self.host = host

            def __call__(self, request: pyramid.request.Request) -> dict[str, Any] | None:
                params = request.params
                display = self.host["display"]
                if "host" not in params or display == params["host"]:
                    url_headers = build_url(
                        "check_collector",
                        f"{self.host['url'].rstrip('/')}/{c2c_base.strip('/')}/health_check",
                        request,
                    )
                    r = requests.get(
                        params={"max_level": str(self.host.get("max_level", max_level))},
                        timeout=120,
                        **url_headers,  # type: ignore[arg-type]
                    )
                    r.raise_for_status()
                    return cast("dict[str, Any]", r.json())
                return None

        health_check.add_custom_check(
            name="check_collector_" + host["display"],
            check_cb=Check(host),
            level=settings["level"],
        )
