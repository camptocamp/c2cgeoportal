import pyramid.request
from pyramid.security import ALL_PERMISSIONS, Allow

from typing import ClassVar


class Root:
    """The Pyramid root object."""

    __acl__: ClassVar[list[tuple[str, str, str]]] = [(Allow, "role_admin", ALL_PERMISSIONS)]

    def __init__(self, request: pyramid.request.Request) -> None:
        self.request = request
