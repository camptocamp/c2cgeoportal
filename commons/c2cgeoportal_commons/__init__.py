"""c2cgeoportal_commons package."""
from typing import Optional  # noqa, pylint: disable=unused-import

from pyramid.config import Configurator

schema = None  # type: Optional[str]
srid = None  # type: Optional[str]


def includeme(config: Configurator) -> None:
    """
    Initialize the model for a Pyramid app.
    Activate this setup using ``config.include('c2cgeoportal_admin.commons')``.
    """
    settings = config.get_settings()
    settings['tm.manager_hook'] = 'pyramid_tm.explicit_manager'

    # use pyramid_tm to hook the transaction lifecycle to the request
    config.include('pyramid_tm')
