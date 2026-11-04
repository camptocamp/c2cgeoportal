"""
Compatibility shim for ``pkg_resources``.

``pkg_resources`` was removed from ``setuptools`` 82 and later.  Several of our
runtime dependencies (``c2cgeoform``, ``deform``, ``lingua``, ...) still import
it, and our own code used it too.  Downgrading ``setuptools`` is not an option
because of the Snyk security floor, so this module provides the small subset of
the ``pkg_resources`` API that we actually use, implemented on top of
``importlib.metadata`` and ``importlib.resources``.

It is installed as a top-level module by ``c2cgeoportal_commons`` so that it is
available in every environment where the GeoMapFish packages are installed.
"""

from __future__ import annotations

import importlib.metadata
import importlib.resources
from collections.abc import Iterator
from typing import Any


class DistributionNotFound(ImportError):
    """Raised when a distribution cannot be found."""


class Distribution:
    """Minimal stand-in for :class:`pkg_resources.Distribution`."""

    def __init__(self, name: str, version: str) -> None:
        self.name = name
        self._version = version

    @property
    def version(self) -> str:
        return self._version

    def __repr__(self) -> str:
        return f"Distribution({self.name!r}, {self.version!r})"


class EntryPoint:
    """Minimal stand-in for :class:`pkg_resources.EntryPoint`."""

    def __init__(self, name: str, value: str, group: str) -> None:
        self.name = name
        self.value = value
        self.group = group

    def load(self, require: bool = False) -> Any:  # noqa: ARG002
        """Import and return the object referenced by the entry point."""
        module_name, _, attr = self.value.partition(":")
        module = __import__(module_name, fromlist=[attr] if attr else [])
        return getattr(module, attr) if attr else module


class WorkingSet:
    """Minimal stand-in for :class:`pkg_resources.WorkingSet`."""

    def iter_entry_points(
        self,
        group: str,
        name: str | None = None,
    ) -> Iterator[EntryPoint]:
        """Iterate over the installed entry points of the given group."""
        # ``entry_points().select`` is available since Python 3.10, which is
        # the minimum version supported by c2cgeoportal.
        selected = importlib.metadata.entry_points().select(group=group)
        for entry_point in selected:
            if name is None or entry_point.name == name:
                yield EntryPoint(entry_point.name, entry_point.value, entry_point.group)


working_set = WorkingSet()


def get_distribution(name: str) -> Distribution:
    """Return the distribution matching ``name``."""
    try:
        distribution = importlib.metadata.distribution(name)
    except importlib.metadata.PackageNotFoundError as exception:
        raise DistributionNotFound(f"Distribution {name!r} not found") from exception
    return Distribution(distribution.metadata["Name"], distribution.version)


def resource_filename(package: str, resource: str) -> str:
    """Return the filesystem path of a resource inside ``package``."""
    try:
        return str(importlib.resources.files(package) / resource)
    except (ModuleNotFoundError, TypeError) as exception:
        raise FileNotFoundError(f"Resource {resource!r} not found in package {package!r}") from exception
