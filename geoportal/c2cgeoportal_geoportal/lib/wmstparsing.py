# -*- coding: utf-8 -*-

# Copyright (c) 2013-2019, Camptocamp SA
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


import isodate
import datetime


class TimeInformation:
    """
    Arguments:

    * ``extent`` A time extent instance (``TimeExtentValue`` or
                 ``TimeExtentInterval``)
    * ``mode`` The layer mode ("single", "range" or "disabled")
    * ``widget`` The layer mode ("slider" (default) or "datepicker")
    """
    def __init__(self):
        self.extent = None
        self.mode = None
        self.widget = None
        self.layer = None

    def merge(self, layer, extent, mode, widget):
        layer_apply = \
            self.layer == layer or \
            (not self.has_time() and extent is not None)

        self.merge_extent(extent)
        self.merge_mode(mode)
        self.merge_widget(widget)

        if layer_apply:
            layer["time"] = self.to_dict()
            self.layer = layer
        elif self.layer is not None:
            del self.layer["time"]
            self.layer = None

    def merge_extent(self, extent):
        if self.extent is not None:
            self.extent.merge(extent)
        else:
            self.extent = extent

    def merge_mode(self, mode):
        if mode != "disabled":
            if self.mode is not None:
                if self.mode != mode:
                    raise ValueError(
                        "Could not mix time mode '{0!s}' and '{1!s}'".format(mode, self.mode)
                    )
            else:
                self.mode = mode

    def merge_widget(self, widget):
        widget = "slider" if not widget else widget

        if self.widget is not None:
            if self.widget != widget:
                raise ValueError(
                    "Could not mix time widget '{0!s}' and '{1!s}'".format(widget, self.widget)
                )
        else:
            self.widget = widget

    def has_time(self):
        return self.extent is not None

    def to_dict(self):
        if self.has_time():
            time = self.extent.to_dict()
            time["mode"] = self.mode
            time["widget"] = self.widget
            return time
        else:
            return None


class TimeExtentValue:
    """
    Represents time as a list of values.
    """
    def __init__(self, values, resolution, min_def_value, max_def_value):
        """
        Arguments:

        * ``values`` A set() of datetime
        * ``resolution`` The resolution from the mapfile time definition
        * ``min_def_value`` the minimum default value as a datetime
        * ``max_def_value`` the maximum default value as a datetime
        """
        self.values = values
        self.resolution = resolution
        self.min_def_value = min_def_value
        self.max_def_value = max_def_value

    def merge(self, extent):
        if not isinstance(extent, TimeExtentValue):
            raise ValueError(
                "Could not mix time defined as a list of "
                "values with other type of definition")
        self.values.update(extent.values)
        self.min_def_value = min(self.min_def_value, extent.min_def_value)
        self.max_def_value = max(self.max_def_value, extent.max_def_value)

    def to_dict(self):
        values = sorted(self.values)
        min_def_value = _format_date(self.min_def_value) \
            if self.min_def_value else None
        max_def_value = _format_date(self.max_def_value) \
            if self.max_def_value else None

        return {
            "minValue": _format_date(values[0]),
            "maxValue": _format_date(values[-1]),
            "values": list(map(_format_date, values)),
            "resolution": self.resolution,
            "minDefValue": min_def_value,
            "maxDefValue": max_def_value,
        }


class TimeExtentInterval:
    """
    Represents time with the help of a start, an end and an interval.
    """
    def __init__(self, start, end, interval, resolution, min_def_value, max_def_value):
        """
        Arguments:

        * ``start`` The start value as a datetime
        * ``end`` The end value as a datetime
        * ``interval`` The interval as a tuple (years, months, days, seconds)
        * ``resolution`` The resolution from the mapfile time definition
        * ``min_def_value`` the minimum default value as a datetime
        * ``max_def_value`` the maximum default value as a datetime
        """
        self.start = start
        self.end = end
        self.interval = interval
        self.resolution = resolution
        self.min_def_value = min_def_value
        self.max_def_value = max_def_value

    def merge(self, extent):
        if not isinstance(extent, TimeExtentInterval):
            raise ValueError(
                "Could not merge time defined as with an "
                " interval with other type of definition")
        if self.interval != extent.interval:
            raise ValueError(
                "Could not merge times defined with a "
                "different interval")
        self.start = min(self.start, extent.start)
        self.end = max(self.end, extent.end)
        self.min_def_value = \
            self.min_def_value if extent.min_def_value is None else \
            extent.min_def_value if self.min_def_value is None else \
            min(self.min_def_value, extent.min_def_value)
        self.max_def_value = \
            self.max_def_value if extent.max_def_value is None else \
            extent.max_def_value if self.max_def_value is None else \
            max(self.max_def_value, extent.max_def_value)

    def to_dict(self):
        min_def_value = _format_date(self.min_def_value) \
            if self.min_def_value is not None else None
        max_def_value = _format_date(self.max_def_value) \
            if self.max_def_value is not None else None

        return {
            "minValue": _format_date(self.start),
            "maxValue": _format_date(self.end),
            "interval": self.interval,
            "resolution": self.resolution,
            "minDefValue": min_def_value,
            "maxDefValue": max_def_value,
        }


def parse_extent(extent, default_values):
    """
    Parse a time extend from OWSLib to a `̀ TimeExtentValue`` or a
    ``TimeExtentInterval``

    Two formats are supported:
    * ['start/end/interval']
    * ['date1', 'date2', ..., 'date N']

    default_values must be a slash separated String from OWSLib's a
    defaulttimeposition
    """
    if len(extent) > 0:
        min_def_value, max_def_value = _parse_default_values(default_values)
        if extent[0].count("/") > 0:
            # case "start/end/interval"
            if len(extent) > 1 or extent[0].count("/") != 2:
                raise ValueError(
                    "Unsupported time definition '{0!s}'".format(extent))
            s, e, i = extent[0].split("/")
            start = _parse_date(s)
            end = _parse_date(e)
            interval = _parse_duration(i)

            return TimeExtentInterval(start[1], end[1], interval, start[0],
                                      min_def_value, max_def_value)
        else:
            # case "value1, value2, ..., valueN"
            dates = [_parse_date(d) for d in extent]
            resolution = dates[0][0]
            values = set(d[1] for d in dates)

            return TimeExtentValue(values, resolution, min_def_value,
                                   max_def_value)
    else:
        raise ValueError("Invalid time extent format '%s'", extent)


def _parse_default_values(default_values):
    """
    Parse the 'default' value from OWSLib's defaulttimeposition
    and return a maximum of two dates. default value must be a
    slash separated String.
    return None on the seconde value if it does not exist.
    """
    if default_values is None:  # pragma: no cover
        return None, None

    def_value = default_values.split("/")

    _, min_def_value = _parse_date(def_value[0])
    max_def_value = None

    if len(def_value) > 1:
        _, max_def_value = _parse_date(def_value[1])

    return min_def_value, max_def_value


def _parse_date(date):
    """
    Parses a string into a tuple containing:

    * the resolution: "year", "month", "day" or "second"
    * the date as a datetime

    The returned datetime always has a timezone (default to UTC)
    """
    resolutions = {
        "year": "%Y",
        "month": "%Y-%m",
        "day": "%Y-%m-%d",
    }

    for resolution, pattern in list(resolutions.items()):
        try:
            dt = datetime.datetime.strptime(date, pattern)
            return resolution, dt.replace(tzinfo=isodate.UTC)
        except Exception:
            pass

    try:
        dt = isodate.parse_datetime(date)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=isodate.UTC)
        return "second", dt
    except Exception:
        raise ValueError("Invalid date format '{0!s}'".format(date))


def _format_date(date):
    assert isinstance(date, datetime.datetime)
    str_ = isodate.datetime_isoformat(date)
    if date.tzinfo is None:
        str_ += "Z"
    return str_


def _parse_duration(duration):
    """
    Parses an ISO 8601 duration (i.e. "P2DT5S") and returns a tuple containing:

    * years
    * months
    * days
    * seconds
    """
    duration = isodate.parse_duration(duration)

    # casting years and months to int as isodate might return a float
    return (
        int(duration.years) if hasattr(duration, "years") else 0,
        int(duration.months) if hasattr(duration, "months") else 0,
        duration.days,
        duration.seconds,
    )
