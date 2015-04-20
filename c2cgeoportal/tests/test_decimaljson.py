import decimal
from unittest import TestCase
from pyramid import testing


class TestDecimalJSON(TestCase):
    def _call_fut(self, **kwargs):
        from c2cgeoportal import DecimalJSON
        fake_info = {}
        return DecimalJSON(**kwargs)(fake_info)

    def test_decimal(self):
        renderer = self._call_fut()
        value = {
            "str": "an str",
            "int": 1,
            "dec": decimal.Decimal("1.2")
        }
        request = testing.DummyRequest()
        result = renderer(value, {"request": request})
        self.assertEqual(
            result, '{"int": 1, "dec": 1.2, "str": "an str"}')
        self.assertEqual(request.response.content_type,
                         "application/json")

    def test_jsonp(self):
        renderer = self._call_fut()
        value = {
            "str": "an str",
            "int": 1,
            "dec": decimal.Decimal("1.2")
        }
        request = testing.DummyRequest()
        request.params["callback"] = "jsonp_cb"
        result = renderer(value, {"request": request})
        self.assertEqual(
            result, 'jsonp_cb({"int": 1, "dec": 1.2, "str": "an str"});')
        self.assertEqual(request.response.content_type, "text/javascript")
