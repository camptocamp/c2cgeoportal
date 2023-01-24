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

# pylint: disable=missing-docstring,attribute-defined-outside-init,protected-access


import datetime
from unittest import TestCase

import isodate


class TestExtent(TestCase):
    def test_parse_values(self):
        from c2cgeoportal_geoportal.lib.wmstparsing import TimeExtentValue, parse_extent

        extent = parse_extent(["2005", "2006"], "2005")
        self.assertTrue(isinstance(extent, TimeExtentValue))

    def test_parse_interval(self):
        from c2cgeoportal_geoportal.lib.wmstparsing import TimeExtentInterval, parse_extent

        extent = parse_extent(["2000/2005/P1Y"], "2002")
        self.assertTrue(isinstance(extent, TimeExtentInterval))

    def test_unsupported_format(self):
        from c2cgeoportal_geoportal.lib.wmstparsing import parse_extent

        self.assertRaises(ValueError, parse_extent, ["2000/2010"], "2002")
        self.assertRaises(ValueError, parse_extent, [], "2002")

    def test_merge_values(self):
        from c2cgeoportal_geoportal.lib.wmstparsing import TimeExtentValue, parse_extent

        e1 = parse_extent(["2000", "2005"], "2000/2005")
        e2 = parse_extent(["2001", "2003"], "2001/2003")
        self.assertTrue(isinstance(e1, TimeExtentValue))
        self.assertTrue(isinstance(e2, TimeExtentValue))
        e1.merge(e2)
        d = e1.to_dict()
        self.assertEqual(
            d,
            {
                "minValue": "2000-01-01T00:00:00Z",
                "maxValue": "2005-01-01T00:00:00Z",
                "resolution": "year",
                "values": [
                    "2000-01-01T00:00:00Z",
                    "2001-01-01T00:00:00Z",
                    "2003-01-01T00:00:00Z",
                    "2005-01-01T00:00:00Z",
                ],
                "minDefValue": "2000-01-01T00:00:00Z",
                "maxDefValue": "2005-01-01T00:00:00Z",
            },
        )

    def test_merge_interval(self):
        from c2cgeoportal_geoportal.lib.wmstparsing import TimeExtentInterval, parse_extent

        e1 = parse_extent(["2000/2005/P1Y"], "2000/2005")
        e2 = parse_extent(["2006/2010/P1Y"], "2006/2010")
        self.assertTrue(isinstance(e1, TimeExtentInterval))
        self.assertTrue(isinstance(e2, TimeExtentInterval))
        e1.merge(e2)
        d = e1.to_dict()
        self.assertEqual(
            d,
            {
                "minValue": "2000-01-01T00:00:00Z",
                "maxValue": "2010-01-01T00:00:00Z",
                "resolution": "year",
                "interval": (1, 0, 0, 0),
                "minDefValue": "2000-01-01T00:00:00Z",
                "maxDefValue": "2010-01-01T00:00:00Z",
            },
        )

    def test_merge_value_interval(self):
        from c2cgeoportal_geoportal.lib.wmstparsing import parse_extent

        tev = parse_extent(["2000", "2001"], "2000")
        tei = parse_extent(["2000/2010/P1Y"], "2002")
        self.assertRaises(ValueError, tev.merge, tei)
        self.assertRaises(ValueError, tei.merge, tev)

    def test_merge_different_intervals(self):
        from c2cgeoportal_geoportal.lib.wmstparsing import parse_extent

        e1 = parse_extent(["2000/2005/P1Y"], "2002")
        e2 = parse_extent(["2006/2010/P1M"], "2002")
        self.assertRaises(ValueError, e1.merge, e2)


class TestParseDate(TestCase):
    def test_parse_date_year(self):
        from c2cgeoportal_geoportal.lib.wmstparsing import _parse_date

        date = _parse_date("2010")
        assert "year" == date[0]
        self.assertEqual(datetime.datetime(2010, 0o1, 0o1, tzinfo=isodate.UTC), date[1])

    def test_parse_date_month(self):
        from c2cgeoportal_geoportal.lib.wmstparsing import _parse_date

        date = _parse_date("2010-02")
        assert "month" == date[0]
        self.assertEqual(datetime.datetime(2010, 0o2, 0o1, tzinfo=isodate.UTC), date[1])

    def test_parse_date(self):
        from c2cgeoportal_geoportal.lib.wmstparsing import _parse_date

        date = _parse_date("2010-02-03")
        assert "day" == date[0]
        self.assertEqual(datetime.datetime(2010, 0o2, 0o3, tzinfo=isodate.UTC), date[1])

    def test_parse_datetime(self):
        from c2cgeoportal_geoportal.lib.wmstparsing import _parse_date

        date = _parse_date("2010-02-03T12:34")
        assert "second" == date[0]
        self.assertEqual(datetime.datetime(2010, 0o2, 0o3, 12, 34, tzinfo=isodate.UTC), date[1])

    def test_parse_datetime_tz(self):
        from c2cgeoportal_geoportal.lib.wmstparsing import _parse_date

        date = _parse_date("2010-02-03T12:34Z")
        assert "second" == date[0]
        self.assertEqual(datetime.datetime(2010, 0o2, 0o3, 12, 34, tzinfo=isodate.UTC), date[1])

    def test_unsupported_format(self):
        from c2cgeoportal_geoportal.lib.wmstparsing import _parse_date

        self.assertRaises(ValueError, _parse_date, "2010-02-03 12:34")


class TestFormat(TestCase):
    def test_format(self):
        from c2cgeoportal_geoportal.lib.wmstparsing import _format_date

        dt = datetime.datetime(2010, 0o2, 0o1, 00, 00)
        assert "2010-02-01T00:00:00Z" == _format_date(dt)

    def test_format_tz(self):
        from c2cgeoportal_geoportal.lib.wmstparsing import _format_date, _parse_date

        dt = _parse_date("2010-02-03T12:34:00+01:00")
        assert "2010-02-03T12:34:00+01:00" == _format_date(dt[1])


class TestParseDuration(TestCase):
    def test_year(self):
        from c2cgeoportal_geoportal.lib.wmstparsing import _parse_duration

        self.assertEqual((2, 0, 0, 0), _parse_duration("P2Y"))

    def test_month(self):
        from c2cgeoportal_geoportal.lib.wmstparsing import _parse_duration

        self.assertEqual((0, 2, 0, 0), _parse_duration("P2M"))

    def test_day(self):
        from c2cgeoportal_geoportal.lib.wmstparsing import _parse_duration

        self.assertEqual((0, 0, 2, 0), _parse_duration("P2D"))

    def test_hour(self):
        from c2cgeoportal_geoportal.lib.wmstparsing import _parse_duration

        self.assertEqual((0, 0, 0, 3600), _parse_duration("PT1H"))

    def test_minute(self):
        from c2cgeoportal_geoportal.lib.wmstparsing import _parse_duration

        self.assertEqual((0, 0, 0, 600), _parse_duration("PT10M"))

    def test_second(self):
        from c2cgeoportal_geoportal.lib.wmstparsing import _parse_duration

        self.assertEqual((0, 0, 0, 10), _parse_duration("PT10S"))

    def test_invalid(self):
        from isodate import ISO8601Error

        from c2cgeoportal_geoportal.lib.wmstparsing import _parse_duration

        self.assertRaises(ISO8601Error, _parse_duration, "10S")


class TestTimeInformation(TestCase):
    def test_merge_modes(self):
        from c2cgeoportal_geoportal.lib.wmstparsing import TimeInformation

        ti = TimeInformation()
        self.assertFalse(ti.has_time())
        self.assertTrue(ti.to_dict() is None)
        ti.merge_mode("single")
        assert ti.mode == "single"
        ti.merge_mode("single")
        assert ti.mode == "single"

    def test_merge_different_modes(self):
        from c2cgeoportal_geoportal.lib.wmstparsing import TimeInformation

        ti = TimeInformation()
        ti.merge_mode("single")
        self.assertRaises(ValueError, ti.merge_mode, "range")

    def test_merge_different_widgets(self):
        from c2cgeoportal_geoportal.lib.wmstparsing import TimeInformation

        ti = TimeInformation()
        ti.merge_widget("single")
        self.assertRaises(ValueError, ti.merge_widget, "datepicker")
