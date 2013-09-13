# -*- coding: utf-8 -*-

import isodate
import datetime


class TimeInformation(object):
    """
    Arguments:

    * ``extent`` A time extent instance (``TimeExtentValue`` or
                 ``TimeExtentInterval``)
    * ``mode`` The layer mode ("single", "range" or "disabled")
    """
    def __init__(self):
        self.extent = None
        self.mode = None

    def merge_extent(self, extent):
        if self.extent:
            self.extent.merge(extent)
        else:
            self.extent = extent

    def merge_mode(self, mode):
        if self.mode:
            if self.mode != mode:
                raise ValueError(
                    "Could not mix time mode '%s' and '%s'"
                    % (mode, self.mode))
        else:
            self.mode = mode

    def has_time(self):
        return self.extent is not None

    def to_dict(self):
        if self.has_time():
            time = self.extent.to_dict()
            time["mode"] = self.mode
            return time
        else:
            return None


class TimeExtentValue(object):
    """
    Represents time as a list of values.
    """
    def __init__(self, values, resolution):
        """
        Arguments:

        * ``values`` A set() of datetime
        * ``resolution`` The resolution from the mapfile time definition
        """
        self.values = values
        self.resolution = resolution

    def merge(self, extent):
        if not isinstance(extent, TimeExtentValue):
            raise ValueError(
                "Could not mix time defined as a list of "
                "values with other type of definition")
        self.values.update(extent.values)

    def to_dict(self):
        values = sorted(self.values)

        return {
            "minValue": _format_date(values[0]),
            "maxValue": _format_date(values[-1]),
            "values": map(_format_date, values),
            "resolution": self.resolution,
        }


class TimeExtentInterval(object):
    """
    Represents time with the help of a start, an end and an interval.
    """
    def __init__(self, start, end, interval, resolution):
        """
        Arguments:

        * ``start`` The start value as a datetime
        * ``end`` The end value as a datetime
        * ``interval`` The interval as a tuple (years, months, days, seconds)
        * ``resolution`` The resolution from the mapfile time definition
        """
        self.start = start
        self.end = end
        self.interval = interval
        self.resolution = resolution

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

    def to_dict(self):
        return {
            "minValue": _format_date(self.start),
            "maxValue": _format_date(self.end),
            "interval": self.interval,
            "resolution": self.resolution,
        }


def parse_extent(extent):
    """
    Parse a time extend from OWSLib to a `̀ TimeExtentValue`` or a
    ``TimeExtentInterval``

    Two formats are supported:
    * ['start/end/interval']
    * ['date1', 'date2', ..., 'date N']
    """
    # TODO handle default value when supported by OWSLib
    if len(extent) > 0:
        if extent[0].count("/") > 0:
            # case "start/end/interval"
            if len(extent) > 1 or extent[0].count("/") != 2:
                raise ValueError(
                    "Unsupported time definition '%s'"
                    % extent)
            s, e, i = extent[0].split("/")
            start = _parse_date(s)
            end = _parse_date(e)
            interval = _parse_duration(i)

            return TimeExtentInterval(start[1], end[1], interval,
                                      start[0])
        else:
            # case "value1, value2, ..., valueN"
            dates = [_parse_date(d) for d in extent]
            resolution = dates[0][0]
            values = set(d[1] for d in dates)

            return TimeExtentValue(values, resolution)
    else:
        raise ValueError("Invalid time extent format '%s'", extent)


def _parse_date(date):
    """
    Parses a string into a tuple containing:

    * the resolution: "year", "month", "day" or "second"
    * the date as a datetime

    The returned datetime always has a timezone (default to UTC)
    """
    resolutions = {
        'year': '%Y',
        'month': '%Y-%m',
        'day': '%Y-%m-%d',
    }

    for resolution, pattern in resolutions.items():
        try:
            dt = datetime.datetime.strptime(date, pattern)
            return resolution, dt.replace(tzinfo=isodate.UTC)
        except:
            pass

    try:
        dt = isodate.parse_datetime(date)
        if not dt.tzinfo:
            dt = dt.replace(tzinfo=isodate.UTC)
        return 'second', dt
    except:
        raise ValueError("Invalid date format '%s'" % date)


def _format_date(date):
    assert isinstance(date, datetime.datetime)
    str = isodate.datetime_isoformat(date)
    if not date.tzinfo:
        str += 'Z'
    return str


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
        int(duration.years) if hasattr(duration, 'years') else 0,
        int(duration.months) if hasattr(duration, 'months') else 0,
        duration.days,
        duration.seconds,
    )
