# Copyright (c) 2026, Camptocamp SA
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

from unittest import TestCase
from unittest.mock import patch

from pyramid.i18n import TranslationString

from c2cgeoportal_commons.lib.literal import Literal, LiteralConcat

_TRANSLATIONS = {
    "Hello": "Bonjour",
    "<ul><li>List</li></ul>": "<ul><li>Liste</li></ul>",
}


class _Request:
    @staticmethod
    def translate(tstring: object, **kwargs: object) -> str:
        del kwargs
        return _TRANSLATIONS.get(str(tstring), str(tstring))


class TestLiteral(TestCase):
    def test_literal(self) -> None:
        literal = Literal(TranslationString("Hello", domain="c2cgeoportal"))
        with patch("c2cgeoportal_commons.lib.literal.get_current_request", return_value=_Request()):
            assert literal.__html__() == "Bonjour"
        assert bool(literal)
        assert not bool(Literal(""))

    def test_literal_concat(self) -> None:
        literal = LiteralConcat(
            TranslationString("Hello", domain="c2cgeoportal"),
            TranslationString("<ul><li>List</li></ul>", domain="c2cgeoportal"),
        )
        with patch("c2cgeoportal_commons.lib.literal.get_current_request", return_value=_Request()):
            assert literal.__html__() == "Bonjour<ul><li>Liste</li></ul>"
        assert bool(literal)
        assert not bool(LiteralConcat())

    def test_literal_concat_of_unknown_translation(self) -> None:
        literal = LiteralConcat("Unknown", " translation")
        with patch("c2cgeoportal_commons.lib.literal.get_current_request", return_value=_Request()):
            assert literal.__html__() == "Unknown translation"
