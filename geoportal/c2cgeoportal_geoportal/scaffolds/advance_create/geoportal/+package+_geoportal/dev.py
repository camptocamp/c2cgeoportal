from pyramid.config import Configurator


def includeme(config: Configurator) -> None:
    """Initialize the development tools for a Pyramid app."""
    del config  # Unused.

    try:
        import ptvsd  # pylint: disable=import-outside-toplevel

        ptvsd.enable_attach(address=("172.17.0.1", 5678))
        # ptvsd.wait_for_attach()
    except ModuleNotFoundError:
        pass
