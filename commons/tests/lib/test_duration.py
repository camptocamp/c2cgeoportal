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

import datetime

import pytest

from c2cgeoportal_commons.lib.duration import parse_duration


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("P7D", datetime.timedelta(days=7)),
        ("PT600S", datetime.timedelta(seconds=600)),
        ("PT3H", datetime.timedelta(hours=3)),
        ("PT1H30M", datetime.timedelta(hours=1, minutes=30)),
        ("1w", datetime.timedelta(weeks=1)),
        ("7d", datetime.timedelta(days=7)),
        ("1d", datetime.timedelta(days=1)),
        ("2h30", datetime.timedelta(hours=2, minutes=30)),
        ("2m30", datetime.timedelta(minutes=2, seconds=30)),
        ("1w2d3h4m5s", datetime.timedelta(weeks=1, days=2, hours=3, minutes=4, seconds=5)),
        ("300", datetime.timedelta(seconds=300)),
        (300, datetime.timedelta(seconds=300)),
        (300.5, datetime.timedelta(seconds=300.5)),
        ("3600", datetime.timedelta(hours=1)),
        (datetime.timedelta(days=2), datetime.timedelta(days=2)),
    ],
)
def test_parse_duration(value, expected) -> None:
    assert parse_duration(value) == expected


@pytest.mark.parametrize("value", ["", "foo", "True", True, False])
def test_parse_duration_invalid(value) -> None:
    with pytest.raises(ValueError, match="Invalid time delta"):
        parse_duration(value)
