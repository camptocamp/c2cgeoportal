# -*- coding: utf-8 -*-

# Copyright (c) 2014-2020, Camptocamp SA
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


from argparse import ArgumentParser
import gettext
import os
import sys
from typing import Any, Dict, List, Set

from sqlalchemy import func
import transaction

from c2cgeoportal_geoportal.scripts import fill_arguments, get_appsettings, get_session


def main():
    parser = ArgumentParser(
        prog=sys.argv[0],
        add_help=True,
        description="Tool to fill the tsearch table (full-text search) from the theme information.",
    )

    locale_path_1 = os.path.join("{package}_geoportal", "locale", "")
    locale_path_2 = os.path.join("geoportal", locale_path_1)
    locale_path = locale_path_2 if os.path.exists("geoportal") else locale_path_1
    parser.add_argument(
        "--locale-folder", default=locale_path, help="The folder where the locale files are stored"
    )
    parser.add_argument("--interfaces", action="append", help="the interfaces to export")
    parser.add_argument(
        "--exclude-interfaces",
        action="append",
        default=["api"],
        help="the interfaces to exclude (can't be used with --interfaces)",
    )
    parser.add_argument(
        "--duplicate-name",
        action="store_true",
        dest="name",
        help="allows to add a name more than one time,\n"
        "by default if we find more than one element with the same name "
        "only one will be imported",
    )
    parser.add_argument("--no-themes", action="store_false", dest="themes", help="do not import the themes")
    parser.add_argument(
        "--no-blocks",
        action="store_false",
        dest="blocks",
        help="do not import the blocks (first level layer groups)",
    )
    parser.add_argument(
        "--no-folders", action="store_false", dest="folders", help="do not import the folders (tree folders)"
    )
    parser.add_argument(
        "--no-layers", action="store_false", dest="layers", help="do not import the layers (tree leaf)"
    )
    parser.add_argument("--package", help="the application package")
    fill_arguments(parser)
    options = parser.parse_args()
    settings = get_appsettings(options)

    with transaction.manager:
        session = get_session(settings, transaction.manager)

        Import(session, settings, options)


class Import:
    def __init__(self, session, settings, options):
        self.options = options
        self.imported: Set[Any] = set()
        package = settings["package"]

        self.fts_languages = settings["fulltextsearch"]["languages"]
        self.languages = settings["available_locale_names"]

        # must be done only once we have loaded the project config
        from c2cgeoportal_commons.models.main import (  # pylint: disable=import-outside-toplevel
            FullTextSearch,
            Interface,
            Theme,
            Role,
        )

        self.session = session
        self.session.execute(FullTextSearch.__table__.delete().where(FullTextSearch.from_theme))  # noqa

        self._: Dict[str, gettext.NullTranslations] = {}
        for lang in self.languages:
            try:
                self._[lang] = gettext.translation(
                    "{}_geoportal-client".format(package),
                    options.locale_folder.format(package=package),
                    [lang],
                )
            except OSError as e:
                self._[lang] = gettext.NullTranslations()
                print("Warning: {} (language: {})".format(e, lang))

        query = self.session.query(Interface)
        if options.interfaces is not None:
            query = query.filter(Interface.name.in_(options.interfaces))
        else:
            query = query.filter(Interface.name.notin_(options.exclude_interfaces))
        self.interfaces = query.all()

        self.public_theme: Dict[int, List[int]] = {}
        self.public_group: Dict[int, List[int]] = {}
        for interface in self.interfaces:
            self.public_theme[interface.id] = []
            self.public_group[interface.id] = []

        for theme in self.session.query(Theme).filter_by(public=True).all():
            self._add_theme(theme)

        for role in self.session.query(Role).all():
            for theme in self.session.query(Theme).all():
                self._add_theme(theme, role)

    def _add_fts(self, item, interface, action, role):
        from c2cgeoportal_commons.models.main import FullTextSearch  # pylint: disable=import-outside-toplevel

        key = (
            item.name if self.options.name else item.id,
            interface.id,
            role.id if role is not None else None,
        )
        if key not in self.imported:
            self.imported.add(key)
            for lang in self.languages:
                fts = FullTextSearch()
                fts.label = self._[lang].gettext(item.name)
                fts.role = role
                fts.interface = interface
                fts.lang = lang
                fts.public = role is None
                fts.ts = func.to_tsvector(self.fts_languages[lang], fts.label)
                fts.actions = [{"action": action, "data": item.name}]
                fts.from_theme = True
                self.session.add(fts)

    def _add_theme(self, theme, role=None):
        fill = False
        for interface in self.interfaces:
            if interface in theme.interfaces:
                for child in theme.children:
                    fill = self._add_block(child, interface, role) or fill

                if fill and self.options.themes:
                    if role is None:
                        self.public_theme[interface.id].append(theme.id)

                    if role is None or theme.id not in self.public_theme[interface.id]:
                        self._add_fts(theme, interface, "add_theme", role)

    def _add_block(self, group, interface, role):
        return self._add_group(group, interface, self.options.blocks, role)

    def _add_folder(self, group, interface, role):
        return self._add_group(group, interface, self.options.folders, role)

    def _add_group(self, group, interface, export, role):
        from c2cgeoportal_commons.models.main import LayerGroup  # pylint: disable=import-outside-toplevel

        fill = False
        for child in group.children:
            if isinstance(child, LayerGroup):
                fill = self._add_folder(child, interface, role) or fill
            else:
                fill = self._add_layer(child, interface, role) or fill

        if fill and export:
            if role is None:
                self.public_group[interface.id].append(group.id)

            if role is None or group.id not in self.public_group[interface.id]:
                self._add_fts(group, interface, "add_group", role)

        return fill

    @staticmethod
    def _layer_visible(layer, role):
        for restrictionarea in layer.restrictionareas:
            if role in restrictionarea.roles:
                return True
        return False

    def _add_layer(self, layer, interface, role):
        if role is None:
            fill = layer.public and interface in layer.interfaces
        else:
            fill = interface in layer.interfaces and not layer.public and self._layer_visible(layer, role)

        if fill and self.options.layers:
            self._add_fts(layer, interface, "add_layer", role)

        return fill
