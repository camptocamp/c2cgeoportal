# -*- coding: utf-8 -*-

# Copyright (c) 2013-2021, Camptocamp SA
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


import urllib.parse
from typing import Dict, Optional, Set

from pyramid.request import Request


def add_url_params(url: str, params: Optional[Dict[str, str]]) -> str:
    if not params:
        return url
    return add_spliturl_params(urllib.parse.urlsplit(url), params)


def add_spliturl_params(spliturl: urllib.parse.SplitResult, params: Dict[str, str]) -> str:
    query = {k: v[-1] for k, v in list(urllib.parse.parse_qs(spliturl.query).items())}
    for key, value in list(params.items()):
        if key not in query:
            query[key] = value

    return urllib.parse.urlunsplit(
        (spliturl.scheme, spliturl.netloc, spliturl.path, urllib.parse.urlencode(query), spliturl.fragment)
    )


def get_url2(name: str, url: str, request: Request, errors: Set[str]) -> Optional[str]:
    url_split = urllib.parse.urlsplit(url)
    if url_split.scheme == "":
        if url_split.netloc == "" and url_split.path not in ("", "/"):
            # Relative URL like: /dummy/static/url or dummy/static/url
            return urllib.parse.urlunsplit(url_split)
        errors.add("{}='{}' is not an URL.".format(name, url))
        return None
    if url_split.scheme in ("http", "https"):
        if url_split.netloc == "":
            errors.add("{}='{}' is not a valid URL.".format(name, url))
            return None
        return urllib.parse.urlunsplit(url_split)
    if url_split.scheme == "static":
        if url_split.path in ("", "/"):
            errors.add("{}='{}' cannot have an empty path.".format(name, url))
            return None
        proj = url_split.netloc
        package = request.registry.settings["package"]
        if proj in ("", "static"):
            proj = "/etc/geomapfish/static"
        elif ":" not in proj:
            if proj == "static-ngeo":
                errors.add(
                    "{}='{}' static-ngeo shouldn't be used out of webpack because it don't has "
                    "cache bustering.".format(name, url)
                )
            proj = "{}_geoportal:{}".format(package, proj)
        return request.static_url("{}{}".format(proj, url_split.path))
    if url_split.scheme == "config":
        if url_split.netloc == "":
            errors.add("{}='{}' cannot have an empty netloc.".format(name, url))
            return None
        server = request.registry.settings.get("servers", {}).get(url_split.netloc)
        if server is None:
            errors.add(
                "{}: The server '{}' ({}) is not found in the config: [{}]".format(
                    name,
                    url_split.netloc,
                    url,
                    ", ".join(request.registry.settings.get("servers", {}).keys()),
                )
            )
            return None

        if isinstance(server, dict):
            url = server["url"]
            params: Dict[str, str] = server.get("params", {})
        else:
            url_split_server = urllib.parse.urlsplit(server)
            params = dict(urllib.parse.parse_qsl(url_split_server.query))
            url = urllib.parse.urlunsplit(url_split_server._replace(query=""))
        params.update(dict(urllib.parse.parse_qsl(url_split.query)))

        if url_split.path != "":
            if url[-1] != "/":
                url += "/"
            url = urllib.parse.urljoin(url, url_split.path[1:])

        return url if not params else "{}?{}".format(url, urllib.parse.urlencode(params))

    return None
