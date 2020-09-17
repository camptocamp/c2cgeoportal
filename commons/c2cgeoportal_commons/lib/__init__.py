from typing import Optional
import urllib.parse


def get_url2(name, url, request, errors) -> Optional[str]:
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
        if url_split.path != "":
            if server[-1] != "/":
                server += "/"
            url = urllib.parse.urljoin(server, url_split.path[1:])
        else:
            url = server
        return url if not url_split.query else "{}?{}".format(url, url_split.query)
    return None
