# Copyright (c) 2013-2023, Camptocamp SA
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


import datetime
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import isodate

TimeExtent = Union["TimeExtentValue", "TimeExtentInterval"]


def min_none(a: Optional[datetime.datetime], b: Optional[datetime.datetime]) -> Optional[datetime.datetime]:
    """Return the min value, support non in input."""
    if a is None:
        return b
    if b is None:
        return a
    return min(a, b)


def max_none(a: Optional[datetime.datetime], b: Optional[datetime.datetime]) -> Optional[datetime.datetime]:
    """Return the max value, support non in input."""
    if a is None:
        return b
    if b is None:
        return a
    return max(a, b)


class TimeInformation:
    """
    Collect the WMS time information.

    Arguments:

        extent: A time extent instance (``TimeExtentValue`` or ``TimeExtentInterval``)
        mode: The layer mode ("single", "range" or "disabled")
        widget: The layer mode ("slider" (default) or "datepicker")
    """

    def __init__(self) -> None:
        self.extent: Optional[TimeExtent] = None
        self.mode: Optional[str] = None
        self.widget: Optional[str] = None
        self.layer: Optional[Dict[str, Any]] = None

    def merge(self, layer: Dict[str, Any], extent: TimeExtent, mode: str, widget: str) -> None:
        layer_apply = self.layer == layer or (not self.has_time() and extent is not None)

        self.merge_extent(extent)
        self.merge_mode(mode)
        self.merge_widget(widget)

        if layer_apply:
            layer["time"] = self.to_dict()
            self.layer = layer
        elif self.layer is not None:
            del self.layer["time"]
            self.layer = None

    def merge_extent(self, extent: TimeExtent) -> None:
        if self.extent is not None:
            self.extent.merge(extent)
        else:
            self.extent = extent

    def merge_mode(self, mode: str) -> None:
        if mode != "disabled":
            if self.mode is not None:
                if self.mode != mode:
                    raise ValueError(f"Could not mix time mode '{mode!s}' and '{self.mode!s}'")
            else:
                self.mode = mode

    def merge_widget(self, widget: Optional[str]) -> None:
        widget = "slider" if not widget else widget
        assert widget is not None

        if self.widget is not None:
            if self.widget != widget:
                raise ValueError(f"Could not mix time widget '{widget!s}' and '{self.widget!s}'")
        else:
            self.widget = widget

    def has_time(self) -> bool:
        return self.extent is not None

    def to_dict(self) -> Optional[Dict[str, Any]]:
        if self.has_time():
            assert self.extent is not None
            time = self.extent.to_dict()
            time["mode"] = self.mode
            time["widget"] = self.widget
            return time
        return None


class TimeExtentValue:
    """Represents time as a list of values."""

    def __init__(
        self,
        values: Set[datetime.datetime],
        resolution: str,
        min_def_value: Optional[datetime.datetime],
        max_def_value: Optional[datetime.datetime],
    ):
        """
        Initialize.

        Arguments:

            values: A set() of datetime
            resolution: The resolution from the mapfile time definition
            min_def_value: the minimum default value as a datetime
            max_def_value: the maximum default value as a datetime
        """
        self.values = values
        self.resolution = resolution
        self.min_def_value = min_def_value
        self.max_def_value = max_def_value

    def merge(self, extent: TimeExtent) -> None:
        if not isinstance(extent, TimeExtentValue):
            raise ValueError("Could not mix time defined as a list of values with other type of definition")
        self.values.update(extent.values)
        self.min_def_value = min_none(self.min_def_value, extent.min_def_value)
        self.max_def_value = max_none(self.max_def_value, extent.max_def_value)

    def to_dict(self) -> Dict[str, Any]:
        values = sorted(self.values)
        min_def_value = _format_date(self.min_def_value) if self.min_def_value else None
        max_def_value = _format_date(self.max_def_value) if self.max_def_value else None

        return {
            "minValue": _format_date(values[0]),
            "maxValue": _format_date(values[-1]),
            "values": list(map(_format_date, values)),
            "resolution": self.resolution,
            "minDefValue": min_def_value,
            "maxDefValue": max_def_value,
        }


class TimeExtentInterval:
    """Represents time with the help of a start, an end and an interval."""

    def __init__(
        self,
        start: datetime.datetime,
        end: datetime.datetime,
        interval: Tuple[int, int, int, int],
        resolution: str,
        min_def_value: Optional[datetime.datetime],
        max_def_value: Optional[datetime.datetime],
    ):
        """
        Initialize.

        Arguments:

            start: The start value as a datetime
            end: The end value as a datetime
            interval: The interval as a tuple (years, months, days, seconds)
            resolution: The resolution from the mapfile time definition
            min_def_value: the minimum default value as a datetime
            max_def_value: the maximum default value as a datetime
        """
        self.start = start
        self.end = end
        self.interval = interval
        self.resolution = resolution
        self.min_def_value = min_def_value
        self.max_def_value = max_def_value

    def merge(self, extent: TimeExtent) -> None:
        if not isinstance(extent, TimeExtentInterval):
            raise ValueError("Could not merge time defined as with an interval with other type of definition")
        if self.interval != extent.interval:
            raise ValueError("Could not merge times defined with a different interval")
        start = min_none(self.start, extent.start)
        assert start is not None
        self.start = start
        end = max_none(self.end, extent.end)
        assert end is not None
        self.end = end
        self.min_def_value = (
            self.min_def_value
            if extent.min_def_value is None
            else extent.min_def_value
            if self.min_def_value is None
            else min_none(self.min_def_value, extent.min_def_value)
        )
        self.max_def_value = (
            self.max_def_value
            if extent.max_def_value is None
            else extent.max_def_value
            if self.max_def_value is None
            else max_none(self.max_def_value, extent.max_def_value)
        )

    def to_dict(self) -> Dict[str, Any]:
        min_def_value = _format_date(self.min_def_value) if self.min_def_value is not None else None
        max_def_value = _format_date(self.max_def_value) if self.max_def_value is not None else None

        return {
            "minValue": _format_date(self.start),
            "maxValue": _format_date(self.end),
            "interval": self.interval,
            "resolution": self.resolution,
            "minDefValue": min_def_value,
            "maxDefValue": max_def_value,
        }


def parse_extent(extent: List[str], default_values: str) -> TimeExtent:
    """
    Parse a time extend from OWSLib to a `̀ TimeExtentValue`` or a ``TimeExtentInterval``.

    Two formats are supported:
    * ['start/end/interval']
    * ['date1', 'date2', ..., 'date N']

    default_values must be a slash separated String from OWSLib's a
    defaulttimeposition
    """
    if extent:
        min_def_value, max_def_value = _parse_default_values(default_values)
        if extent[0].count("/") > 0:
            # case "start/end/interval"
            if len(extent) > 1 or extent[0].count("/") != 2:
                raise ValueError(f"Unsupported time definition '{extent!s}'")
            s, e, i = extent[0].split("/")
            start = _parse_date(s)
            end = _parse_date(e)
            interval = _parse_duration(i)

            return TimeExtentInterval(start[1], end[1], interval, start[0], min_def_value, max_def_value)
        # case "value1, value2, ..., valueN"
        dates = [_parse_date(d) for d in extent]
        resolution = dates[0][0]
        values = {d[1] for d in dates}

        return TimeExtentValue(values, resolution, min_def_value, max_def_value)
    raise ValueError(f"Invalid time extent format '{extent}'")


def _parse_default_values(default_values: str) -> Tuple[datetime.datetime, Optional[datetime.datetime]]:
    """
    Parse the 'default' value from OWSLib's defaulttimeposition and return a maximum of two dates.

    default value must be a slash separated String. return None on the seconde value if it does not exist.
    """
    if default_values is None:
        return None, None

    def_value = default_values.split("/")

    _, min_def_value = _parse_date(def_value[0])
    max_def_value = None

    if len(def_value) > 1:
        _, max_def_value = _parse_date(def_value[1])

    return min_def_value, max_def_value


def _parse_date(date: str) -> Tuple[str, datetime.datetime]:
    """
    Parse a date string.

    Return a tuple containing:

    * the resolution: "year", "month", "day" or "second"
    * the date as a datetime

    The returned datetime always has a timezone (default is UTC)
    """
    resolutions = {"year": "%Y", "month": "%Y-%m", "day": "%Y-%m-%d"}

    for resolution, pattern in list(resolutions.items()):
        try:
            dt = datetime.datetime.strptime(date, pattern)
            return resolution, dt.replace(tzinfo=isodate.UTC)
        except Exception:  # nosec
            pass

    try:
        dt = isodate.parse_datetime(date)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=isodate.UTC)
        return "second", dt
    except Exception as e:
        raise ValueError(f"Invalid date format '{date}'") from e


def _format_date(date: datetime.datetime) -> str:
    str_ = isodate.datetime_isoformat(date)
    assert isinstance(str_, str)
    if date.tzinfo is None:
        str_ += "Z"
    return str_


def _parse_duration(duration: str) -> Tuple[int, int, int, int]:
    """
    Parse an ISO 8601 duration (i.e. "P2DT5S").

    Return a tuple containing:

    * years
    * months
    * days
    * seconds
    """
    parsed_duration = isodate.parse_duration(duration)

    # casting years and months to int as isodate might return a float
    return (
        int(parsed_duration.years) if hasattr(parsed_duration, "years") else 0,
        int(parsed_duration.months) if hasattr(parsed_duration, "months") else 0,
        parsed_duration.days,
        parsed_duration.seconds,
    )
