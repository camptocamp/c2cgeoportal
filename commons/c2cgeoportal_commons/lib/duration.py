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

"""Parse a duration expressed as a string or a number of seconds into a ``datetime.timedelta``."""

import datetime
import re

_ISO_DURATION_RE = re.compile(
    r"^P(?:(\d+)Y)?(?:(\d+)M)?(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+(?:\.\d+)?)S)?)?$",
)
_SHORT_DURATION_RE = re.compile(r"(\d+)([wdhms])?")


def _unit_to_name(unit: str) -> str:
    return {"w": "weeks", "d": "days", "h": "hours", "m": "minutes", "s": "seconds"}[unit]


def _next_unit(unit: str) -> str:
    order = ["w", "d", "h", "m", "s"]
    idx = order.index(unit)
    return _unit_to_name(order[idx + 1]) if idx + 1 < len(order) else "seconds"


def parse_duration(text: str | datetime.timedelta | float) -> datetime.timedelta:
    """
    Parse a duration to a timedelta.

    Supports the ISO 8601 duration format (e.g. PT3H, P30D, PT600S),
    the short format (e.g. 2h30, 2m30, 1d, 1w, 1w2d3h4m5s), a plain number
    of seconds as a string (e.g. "300") or as an int or float.
    The supported units are: w (weeks), d (days), h (hours), m (minutes), s (seconds).
    When the last number has no unit, it takes the next logical unit
    (e.g. 2h30 = 2h30m, 2m30 = 2m30s).
    """
    if isinstance(text, datetime.timedelta):
        return text
    if isinstance(text, bool):
        # A boolean is not a valid duration; as bool is a subclass of int, it must be rejected
        # before the numeric handling; ValueError to match invalid string values.
        message = f"Invalid time delta: {text}"
        raise ValueError(message)  # noqa: TRY004
    if isinstance(text, (int, float)):
        return datetime.timedelta(seconds=text)
    match = _ISO_DURATION_RE.match(text)
    if match:
        parts = match.groups()
        return datetime.timedelta(
            days=int(parts[2] or 0),
            hours=int(parts[3] or 0),
            minutes=int(parts[4] or 0),
            seconds=float(parts[5] or 0),
        )
    segments = _SHORT_DURATION_RE.findall(text)
    if segments:
        kwargs: dict[str, int] = {}
        last_unit = "s"
        for value, unit in segments:
            if unit:
                kwargs.setdefault(_unit_to_name(unit), int(value))
                last_unit = unit
            else:
                kwargs.setdefault(_next_unit(last_unit), int(value))
        return datetime.timedelta(**kwargs)
    message = f"Invalid time delta: {text}"
    raise ValueError(message)
