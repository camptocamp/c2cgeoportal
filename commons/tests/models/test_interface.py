# pylint: disable=no-self-use

import pytest


@pytest.mark.usefixtures("transact")
class TestInterface:
    def test_delete_cascade_to_tsearch(self, dbsession) -> None:
        from c2cgeoportal_commons.models.main import FullTextSearch, Interface
        from sqlalchemy import func

        interface = Interface("desktop", "Desktop interface")
        interface_id = interface.id

        fts = FullTextSearch()
        fts.label = "Text to search"
        fts.interface = interface
        fts.ts = func.to_tsvector("french", fts.label)
        dbsession.add(fts)
        dbsession.flush()

        dbsession.delete(interface)
        dbsession.flush()

        assert (
            dbsession.query(FullTextSearch).filter(FullTextSearch.interface_id == interface_id).count() == 0
        )
