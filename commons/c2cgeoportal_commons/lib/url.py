# Copyright (c) 2013-2024, Camptocamp SA
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
import re
import urllib.parse

from pyramid.request import Request

_LOG = logging.getLogger(__name__)


class Url:
    """Object representation of an URI."""

    scheme = ""
    _netloc = ""
    _hostname: str | None = None
    _port: int | None = None
    path = ""
    query: dict[str, str] = {}
    fragment = ""

    def __init__(self, url: str | None = None):
        if url:
            url_split = urllib.parse.urlsplit(url)
            self.scheme = url_split.scheme
            self._netloc = url_split.netloc
            self._hostname = url_split.hostname
            try:
                self._port = url_split.port
            except ValueError as error:
                _LOG.debug(error)
            self.path = url_split.path
            self.query = dict(urllib.parse.parse_qsl(url_split.query))
            self.fragment = url_split.fragment

    def clone(self) -> "Url":
        result = Url()
        result.scheme = self.scheme
        result._netloc = self._netloc  # pylint: disable=protected-access
        result._hostname = self._hostname  # pylint: disable=protected-access
        result._port = self._port  # pylint: disable=protected-access
        result.path = self.path
        result.query = dict(self.query)
        result.fragment = self.fragment
        return result

    @staticmethod
    def _is_valid_hostname(hostname: str) -> bool:
        if len(hostname) > 255:
            return False
        if hostname[-1] == ".":
            hostname = hostname[:-1]  # strip exactly one dot from the right, if present
        allowed = re.compile(r"(?!-)[a-z\d-]{1,63}(?<!-)$", re.IGNORECASE)
        return all(allowed.match(x) for x in hostname.split("."))

    @property
    def netloc(self) -> str:
        return self._netloc

    @netloc.setter
    def netloc(self, netloc: str) -> None:
        netloc_split = netloc.split(":")
        if len(netloc_split) > 2:
            raise RuntimeError(f"The netloc '{netloc}' in invalid")
        if not self._is_valid_hostname(netloc_split[0]):
            raise RuntimeError(f"The netloc '{netloc}' in invalid")
        if len(netloc_split) == 2:
            allowed = re.compile(r"^[0-9]+$")
            if not allowed.match(netloc_split[1]):
                _LOG.debug("The netloc '%s' contains invalid port", netloc)
                self._port = None
            else:
                self._port = int(netloc_split[1])
        else:
            self._port = None
        self._netloc = netloc
        self._hostname = netloc_split[0]

    @property
    def hostname(self) -> str | None:
        return self._hostname

    @hostname.setter
    def hostname(self, hostname: str) -> None:
        if not self._is_valid_hostname(hostname):
            raise RuntimeError(f"The hostname '{hostname}' in invalid")
        self._hostname = hostname
        self.netloc = hostname if self._port is None else f"{hostname}:{self._port}"

    @property
    def port(self) -> int | None:
        return self._port

    @port.setter
    def port(self, port: int | None) -> None:
        self._port = port
        self.netloc = (self._hostname or "") if port is None else f"{self._hostname}:{port}"

    def add_query(self, query: dict[str, str], force: bool = False) -> "Url":
        if query:
            for key, value in query.items():
                if force or key not in self.query:
                    self.query[key] = value
        return self

    @property
    def query_lower(self) -> dict[str, str]:
        return {k.lower(): v for k, v in self.query.items()}

    def url(self) -> str:
        return urllib.parse.urlunsplit(
            (
                self.scheme,
                self._netloc,
                self.path,
                urllib.parse.urlencode(self.query),
                self.fragment,
            )
        )

    def __str__(self) -> str:
        return self.url()

    def __repr__(self) -> str:
        return self.url()


def get_url2(
    name: str, url: str, request: Request, errors: set[str], servers: dict[str, str] | None = None
) -> Url | None:
    """
    Get the real URL from the URI of the administration interface.

    Manage the schema: static and config.
    """
    if servers is None:
        servers = request.registry.settings.get("servers", {})

    url_obj = Url(url)
    url_split = urllib.parse.urlsplit(url)
    if url_obj.scheme == "":
        if url_obj.netloc == "" and url_obj.path not in ("", "/"):
            # Relative URL like: /dummy/static/url or dummy/static/url
            return url_obj
        errors.add(f"{name}='{url}' is not an URL.")
        return None
    if url_obj.scheme in ("http", "https"):
        if url_obj.netloc == "":
            errors.add(f"{name}='{url}' is not a valid URL.")
            return None
        return url_obj
    if url_obj.scheme == "static":
        if request is None:
            errors.add(f"{name}='{url}' The request is required for static URL.")
        if url_obj.path in ("", "/"):
            errors.add(f"{name}='{url}' cannot have an empty path.")
            return None
        proj = url_obj.netloc
        package = request.registry.settings["package"]
        if proj in ("", "static"):
            proj = "/etc/geomapfish/static"
        elif ":" not in proj:
            if proj == "static-ngeo":
                errors.add(
                    f"{name}='{url}' static-ngeo shouldn't be used out of webpack because it don't has "
                    "cache bustering."
                )
            proj = f"{package}_geoportal:{proj}"
        return Url(request.static_url(f"{proj}{url_split.path}"))
    if url_obj.scheme == "config":
        if url_obj.netloc == "":
            errors.add(f"{name}='{url}' cannot have an empty netloc.")
            return None
        server = servers.get(url_obj.netloc)
        if server is None:
            errors.add(
                f"{name}: The server '{url_obj.netloc}' ({url}) is not found in the config: "
                f"[{', '.join(servers.keys())}]"
            )
            return None

        if isinstance(server, dict):
            url_obj_server = Url(server["url"])
            url_obj_server.add_query(server.get("params", {}))
        else:
            url_obj_server = Url(server)

        if url_obj.path != "":
            if url_obj_server.path == "" or url_obj_server.path[-1] != "/":
                url_obj_server.path += "/"
            url_obj_server.path = urllib.parse.urljoin(url_obj_server.path, url_obj.path[1:])
        url_obj_server.add_query(url_obj.query, force=True)
        url_obj_server.fragment = url_obj.fragment
        return url_obj_server
    return None
