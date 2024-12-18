from pyramid.config import Configurator


def includeme(config: Configurator) -> None:
    """Initialize the multi-tenant."""

    del config  # Unused
