# pylint: disable=no-self-use

import pytest

from c2cgeoportal_commons.lib.validators import url


class TestUrl:
    @pytest.mark.parametrize(
        "valid_url",
        [
            "http://geomapfish.org",
            "https://geomapfish.org/functionalities",
            "geomapfish.org/functionalities",
            "static://img/cadastre.jpeg",
            "config://internal/mapserv",
        ],
    )
    def test_valid_url(self, valid_url):
        url(None, valid_url)
