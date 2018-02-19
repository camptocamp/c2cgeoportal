"""c2cgeoportal_commons package."""
from typing import Optional  # noqa, pylint: disable=unused-import

from pyramid.config import Configurator

from c2cgeoportal_commons.models import (  # noqa
    get_session_factory,
    get_engine,
    get_tm_session,
    generate_mappers,
    init_dbsessions,
)

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

    # use pyramid_retry to retry a request when transient exceptions occur
    config.include('pyramid_retry')

    session_factory = get_session_factory(get_engine(settings))
    config.registry['dbsession_factory'] = session_factory

    # make request.dbsession available for use in Pyramid
    config.add_request_method(
        # r.tm is the transaction manager used by pyramid_tm
        lambda r: get_tm_session(session_factory, r.tm),
        'dbsession',
        reify=True
    )

    generate_mappers()
