from unittest import TestCase
from unittest.mock import patch

from c2cgeoportal_geoportal.lib.i18n import available_locale_names

example_locale_content = {
    ("de", True),
    ("en", True),
    ("fr", True),
    (".emptyfolder", False),
    ("geomapfish_geoportal-client.pot", False),
}


class TestI18n(TestCase):
    @patch("c2cgeoportal_geoportal.lib.i18n.os.path.exists", return_value=True)
    @patch(
        "c2cgeoportal_geoportal.lib.i18n.os.listdir",
        return_value=[locale[0] for locale in example_locale_content],
    )
    @patch(
        "c2cgeoportal_geoportal.lib.i18n.os.path.isdir",
        side_effect=[locale[1] for locale in example_locale_content],
    )
    def test_available_locale_names(self, isdir_mock, listdir_mock, exists_mock):
        locales = available_locale_names()
        self.assertEqual(set(locales), {"de", "en", "fr"})

    def test_available_locale_names_no_dir(self):
        locales = available_locale_names()
        assert locales == []
