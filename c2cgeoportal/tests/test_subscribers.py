from unittest import TestCase
from pyramid import testing


class TestSubscribers(TestCase):

    def test_add_renderer_globals(self):
        from c2cgeoportal.subscribers import add_renderer_globals

        request = testing.DummyRequest()
        request.translate = "translate"
        request.localizer = "localizer"
        event = dict(request=request)
        add_renderer_globals(event)
        self.assertTrue("_" in event)
        self.assertTrue("localizer" in event)
        self.assertEqual(event["_"], "translate")
        self.assertEqual(event["localizer"], "localizer")

    def test_add_localizer(self):
        from c2cgeoportal.subscribers import add_localizer

        request = testing.DummyRequest()

        class Event:
            request = None
        event = Event()
        event.request = request
        add_localizer(event)

        self.assertEqual(request.localizer.translate("test"), "test")
        self.assertEqual(request.translate("test"), "test")
