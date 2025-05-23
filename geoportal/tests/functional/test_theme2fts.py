# Copyright (c) 2020-2025, Camptocamp SA
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# The views and conclusions contained in the software and documentation are those
# of the authors and should not be interpreted as representing official policies,
# either expressed or implied, of the FreeBSD Project.

# pylint: disable=missing-docstring

import logging
from collections import namedtuple
from unittest.mock import patch

import pytest
from c2c.template.config import config as configuration

from tests.functional import setup_common as setup_module

_LOGGER = logging.getLogger(__name__)


@pytest.fixture(scope="module")
def settings():
    setup_module()
    return {
        **configuration.get_config(),
        "available_locale_names": ["fr", "en", "de", "it"],
        "fulltextsearch": {
            "languages": {
                "fr": "french",
                "en": "english",
                "de": "german",
                "it": "italian",
            },
        },
    }


def add_parent(dbsession_old, item, group) -> None:
    """Utility function to add a TreeItem in a TreeGroup."""
    from c2cgeoportal_commons.models import main

    dbsession_old.add(main.LayergroupTreeitem(group=group, item=item, ordering=len(group.children_relation)))


@pytest.fixture
def test_data(dbsession_old, transact_old):
    from c2cgeoportal_commons.models import main

    ogc_server = main.OGCServer(name="ogc_server")
    dbsession_old.add(ogc_server)

    interfaces = {i.name: i for i in [main.Interface(name=name) for name in ["desktop", "mobile", "api"]]}
    dbsession_old.add_all(interfaces.values())

    role = main.Role(name="role")
    dbsession_old.add(role)

    public_theme = main.Theme(name="public_theme")
    public_theme.interfaces = list(interfaces.values())

    private_theme = main.Theme(name="private_theme")
    private_theme.public = False
    private_theme.interfaces = list(interfaces.values())
    private_theme.restricted_roles = [role]

    themes = {t.name: t for t in [public_theme, private_theme]}
    dbsession_old.add_all(themes.values())

    first_level_group = main.LayerGroup(name="first_level_group")
    add_parent(dbsession_old, first_level_group, public_theme)
    add_parent(dbsession_old, first_level_group, private_theme)

    second_level_group = main.LayerGroup(name="second_level_group")
    add_parent(dbsession_old, second_level_group, first_level_group)

    groups = {g.name: g for g in [first_level_group, second_level_group]}
    dbsession_old.add_all(groups.values())

    public_layer = main.LayerWMS(name="public_layer")
    public_layer.ogc_server = ogc_server
    public_layer.interfaces = list(interfaces.values())
    add_parent(dbsession_old, public_layer, first_level_group)

    private_layer = main.LayerWMS(name="private_layer", public=False)
    private_layer.ogc_server = ogc_server
    private_layer.interfaces = list(interfaces.values())
    add_parent(dbsession_old, private_layer, second_level_group)

    layers = {layer.name: layer for layer in [public_layer, private_layer]}
    dbsession_old.add_all(layers.values())

    ra = main.RestrictionArea(name="ra")
    ra.roles = [role]
    ra.layers = [private_layer]
    dbsession_old.add(ra)

    dbsession_old.flush()  # Flush here to detect integrity errors now.

    return {
        "ogc_server": ogc_server,
        "interfaces": interfaces,
        "role": role,
        "themes": themes,
        "groups": groups,
        "layers": layers,
        "restriction_area": ra,
    }


def options(**kwargs):
    default_options = {
        "locale_folder": "locale_folder",
        "interfaces": None,
        "exclude_interfaces": ["api"],
        "name": False,
        "themes": True,
        "blocks": True,
        "folders": True,
        "layers": True,
        "package": "Seems not used",
        "stats": False,
    }
    Options = namedtuple("Options", default_options.keys())
    return Options(**{**default_options, **kwargs})


@pytest.fixture(scope="module")
def dummy_translation():
    """
    Mock gettext.translation to return a dummy Translation class, with a gettext method that returns passed
    text suffixed by language.

    Ex: "public_theme" => "public_theme_fr"
    """

    class Translation:
        def __init__(self, lang) -> None:
            self._lang = lang

        def gettext(self, text):
            return f"{text}_{self._lang}"

    def translation(domain, localedir=None, languages=None):
        return Translation(languages[0])

    with patch(
        "c2cgeoportal_geoportal.scripts.theme2fts.gettext.translation",
        side_effect=translation,
    ) as tr_mock:
        yield tr_mock


@pytest.mark.usefixtures("test_data", "dummy_translation")
class TestImport:
    def assert_fts(self, dbsession_old, attrs) -> None:
        from c2cgeoportal_commons.models import main

        fts = (
            dbsession_old.query(main.FullTextSearch)
            .filter(main.FullTextSearch.label == attrs["label"])
            .filter(main.FullTextSearch.interface == attrs["interface"])
            .filter(main.FullTextSearch.role == attrs["role"])
            .filter(main.FullTextSearch.lang == attrs["lang"])
            .one_or_none()
        )
        assert fts is not None, "No row found for ('{label}', '{interface}', '{role}', '{lang}')".format(
            label=attrs["label"],
            interface=attrs["interface"].name,
            role=attrs["role"].name if attrs["role"] is not None else None,
            lang=attrs["lang"],
        )
        assert fts.layer_name is None
        assert fts.public == attrs["public"]
        assert fts.ts == attrs["ts"][attrs["lang"]]
        assert fts.the_geom is None
        assert fts.params is None
        assert fts.actions == attrs["actions"]
        assert fts.from_theme is True

    def test_import(self, dbsession_old, settings, test_data) -> None:
        from c2cgeoportal_commons.models import main
        from c2cgeoportal_geoportal.scripts.theme2fts import Import

        Import(dbsession_old, settings, options())

        # languages * interfaces * (themes + groups + layers)
        total = 4 * 2 * (1 + 1 + 1)
        # private: languages * interfaces * (themes + layers) * roles
        total += 4 * 2 * (1 + 1) * 5
        assert dbsession_old.query(main.FullTextSearch).count() == total, "\n".join(
            [
                ", ".join((fts.label, str(fts.lang), str(fts.interface), str(fts.public), str(fts.role)))
                for fts in dbsession_old.query(main.FullTextSearch).all()
            ],
        )

        for lang in settings["available_locale_names"]:
            for interface in test_data["interfaces"].values():
                if interface.name == "api":
                    continue
                expected = [
                    {
                        "label": f"public_theme_{lang}",
                        "role": None,
                        "interface": interface,
                        "lang": lang,
                        "public": True,
                        "ts": {
                            "fr": "'fr':3 'public':1 'them':2",
                            "en": "'en':3 'public':1 'theme':2",
                            "de": "'de':3 'public':1 'them':2",
                            "it": "'it':3 'public':1 'them':2",
                        },
                        "actions": [{"action": "add_theme", "data": "public_theme"}],
                    },
                    {
                        "label": f"private_theme_{lang}",
                        "role": test_data["role"],
                        "interface": interface,
                        "lang": lang,
                        "public": False,
                        "ts": {
                            "fr": "'fr':3 'privat':1 'them':2",
                            "en": "'en':3 'privat':1 'theme':2",
                            "de": "'de':3 'privat':1 'them':2",
                            "it": "'it':3 'priv':1 'them':2",
                        },
                        "actions": [{"action": "add_theme", "data": "private_theme"}],
                    },
                    {
                        "label": f"first_level_group_{lang}",
                        "role": None,
                        "interface": interface,
                        "lang": lang,
                        "public": True,
                        "ts": {
                            "fr": "'first':1 'fr':4 'group':3 'level':2",
                            "en": "'en':4 'first':1 'group':3 'level':2",
                            "de": "'de':4 'first':1 'group':3 'level':2",
                            "it": "'first':1 'group':3 'it':4 'level':2",
                        },
                        "actions": [{"action": "add_group", "data": "first_level_group"}],
                    },
                    {
                        "label": f"second_level_group_{lang}",
                        "role": test_data["role"],
                        "interface": interface,
                        "lang": lang,
                        "public": False,
                        "ts": {
                            "fr": "'fr':4 'group':3 'level':2 'second':1",
                            "en": "'en':4 'group':3 'level':2 'second':1",
                            "de": "'de':4 'group':3 'level':2 'second':1",
                            "it": "'group':3 'it':4 'level':2 'second':1",
                        },
                        "actions": [{"action": "add_group", "data": "second_level_group"}],
                    },
                    {
                        "label": f"public_layer_{lang}",
                        "role": None,
                        "interface": interface,
                        "lang": lang,
                        "public": True,
                        "ts": {
                            "fr": "'fr':3 'lai':2 'public':1",
                            "en": "'en':3 'layer':2 'public':1",
                            "de": "'de':3 'lay':2 'public':1",
                            "it": "'it':3 'layer':2 'public':1",
                        },
                        "actions": [{"action": "add_layer", "data": "public_layer"}],
                    },
                    {
                        "label": f"private_layer_{lang}",
                        "role": test_data["role"],
                        "interface": interface,
                        "lang": lang,
                        "public": False,
                        "ts": {
                            "fr": "'fr':3 'lai':2 'privat':1",
                            "en": "'en':3 'layer':2 'privat':1",
                            "de": "'de':3 'lay':2 'privat':1",
                            "it": "'it':3 'layer':2 'priv':1",
                        },
                        "actions": [{"action": "add_layer", "data": "private_layer"}],
                    },
                ]
                for e in expected:
                    self.assert_fts(dbsession_old, e)

    def test_search_alias(self, dbsession_old, settings, test_data) -> None:
        from c2cgeoportal_commons.models import main
        from c2cgeoportal_geoportal.scripts.theme2fts import Import

        alias_layer = main.LayerWMS(name="alias_layer")
        alias_layer.ogc_server = test_data["ogc_server"]
        alias_layer.interfaces = list(test_data["interfaces"].values())
        add_parent(dbsession_old, alias_layer, test_data["groups"]["first_level_group"])
        alias_layer.metadatas = [
            main.Metadata(name="searchAlias", value="myalias,mykeyword"),
            main.Metadata(name="searchAlias", value="myotheralias,myotherkeyword"),
        ]
        dbsession_old.add(alias_layer)
        dbsession_old.flush()

        Import(dbsession_old, settings, options())

        for lang in settings["available_locale_names"]:
            for interface in test_data["interfaces"].values():
                if interface.name == "api":
                    continue
                expected = [
                    {
                        "label": f"alias_layer_{lang}",
                        "role": None,
                        "interface": interface,
                        "lang": lang,
                        "public": True,
                        "ts": {
                            "fr": "'ali':1 'fr':3 'lai':2 'myali':4 'mykeyword':5 'myotherali':6 'myotherkeyword':7",
                            "en": "'alia':1 'en':3 'layer':2 'myalia':4 'mykeyword':5 'myotheralia':6 'myotherkeyword':7",
                            "de": "'alias':1 'de':3 'lay':2 'myalias':4 'mykeyword':5 'myotheralias':6 'myotherkeyword':7",
                            "it": "'alias':1 'it':3 'layer':2 'myalias':4 'mykeyword':5 'myotheralias':6 'myotherkeyword':7",
                        },
                        "actions": [{"action": "add_layer", "data": "alias_layer"}],
                    },
                ]
                for e in expected:
                    self.assert_fts(dbsession_old, e)

    def test_search_label_pattern(self, dbsession_old, settings, test_data) -> None:
        from c2cgeoportal_commons.models import main
        from c2cgeoportal_geoportal.scripts.theme2fts import Import

        label_theme = main.Theme(name="label_theme")
        label_theme.interfaces = list(test_data["interfaces"].values())
        label_theme.metadatas = [
            main.Metadata(name="searchLabelPattern", value="{name}, {theme}"),
        ]
        dbsession_old.add(label_theme)

        label_block = main.LayerGroup(name="label_block")
        add_parent(dbsession_old, label_block, label_theme)
        label_block.metadatas = [
            main.Metadata(name="searchLabelPattern", value="{name} ({theme}, {parent})"),
        ]
        dbsession_old.add(label_block)

        label_group = main.LayerGroup(name="label_group")
        add_parent(dbsession_old, label_group, label_block)
        label_group.metadatas = [
            main.Metadata(name="searchLabelPattern", value="{name} ({theme}, {block}, {parent})"),
        ]
        dbsession_old.add(label_group)

        label_layer = main.LayerWMS(name="label_layer")
        label_layer.ogc_server = test_data["ogc_server"]
        label_layer.interfaces = list(test_data["interfaces"].values())
        add_parent(dbsession_old, label_layer, label_group)
        label_layer.metadatas = [
            main.Metadata(name="searchLabelPattern", value="{name} ({theme}, {block}, {parent})"),
        ]

        dbsession_old.add(label_layer)
        dbsession_old.flush()

        Import(dbsession_old, settings, options())

        for lang in settings["available_locale_names"]:
            for interface in test_data["interfaces"].values():
                if interface.name == "api":
                    continue
                expected = [
                    {
                        "label": f"label_theme_{lang}, label_theme_{lang}",
                        "role": None,
                        "interface": interface,
                        "lang": lang,
                        "public": True,
                        "ts": {
                            "fr": "'fr':3 'label':1 'them':2",
                            "en": "'en':3 'label':1 'theme':2",
                            "de": "'de':3 'label':1 'them':2",
                            "it": "'it':3 'label':1 'them':2",
                        },
                        "actions": [{"action": "add_theme", "data": "label_theme"}],
                    },
                    {
                        "label": f"label_block_{lang} (label_theme_{lang}, label_theme_{lang})",
                        "role": None,
                        "interface": interface,
                        "lang": lang,
                        "public": True,
                        "ts": {
                            "fr": "'block':2 'fr':3 'label':1",
                            "en": "'block':2 'en':3 'label':1",
                            "de": "'block':2 'de':3 'label':1",
                            "it": "'block':2 'it':3 'label':1",
                        },
                        "actions": [{"action": "add_group", "data": "label_block"}],
                    },
                    {
                        "label": f"label_group_{lang} (label_theme_{lang}, label_block_{lang}, label_block_{lang})",
                        "role": None,
                        "interface": interface,
                        "lang": lang,
                        "public": True,
                        "ts": {
                            "fr": "'fr':3 'group':2 'label':1",
                            "en": "'en':3 'group':2 'label':1",
                            "de": "'de':3 'group':2 'label':1",
                            "it": "'group':2 'it':3 'label':1",
                        },
                        "actions": [{"action": "add_group", "data": "label_group"}],
                    },
                    {
                        "label": f"label_layer_{lang} (label_theme_{lang}, label_block_{lang}, label_group_{lang})",
                        "role": None,
                        "interface": interface,
                        "lang": lang,
                        "public": True,
                        "ts": {
                            "fr": "'fr':3 'label':1 'lai':2",
                            "en": "'en':3 'label':1 'layer':2",
                            "de": "'de':3 'label':1 'lay':2",
                            "it": "'it':3 'label':1 'layer':2",
                        },
                        "actions": [{"action": "add_layer", "data": "label_layer"}],
                    },
                ]
                for e in expected:
                    self.assert_fts(dbsession_old, e)
