# -*- coding: utf-8 -*-
from unittest import TestCase
from nose.plugins.attrib import attr

from pyramid import testing

from c2cgeoportal.tests.functional import tearDownModule, setUpModule

@attr(functional=True)
class TestFulltextsearchView(TestCase):

    def setUp(self):
        self.config = testing.setUp(
                settings=dict(default_locale_name='fr')
                )

        import transaction
        from sqlalchemy import func
        from geoalchemy import WKTSpatialElement
        from c2cgeoportal.models import FullTextSearch
        from c2cgeoportal.models import DBSession

        entry = FullTextSearch()
        entry.label = 'label'
        entry.layer_name = 'layer'
        entry.ts = func.to_tsvector('french', 'soleil travail')
        entry.the_geom = WKTSpatialElement("POINT(-90 -45)")

        DBSession.add_all([entry])
        transaction.commit()

    def tearDown(self):
        testing.tearDown()

        import transaction
        from c2cgeoportal.models import FullTextSearch
        from c2cgeoportal.models import DBSession

        DBSession.query(FullTextSearch) \
                .filter(FullTextSearch.label == 'label').delete()
        transaction.commit()

    def test_no_default_laguage(self):
        from pyramid.httpexceptions import HTTPInternalServerError
        from c2cgeoportal.views.fulltextsearch import fulltextsearch

        del(self.config.registry.settings['default_locale_name'])
        request = testing.DummyRequest()
        response = fulltextsearch(request)
        self.assertTrue(isinstance(response, HTTPInternalServerError))

    def test_unknown_laguage(self):
        from pyramid.httpexceptions import HTTPInternalServerError
        from c2cgeoportal.views.fulltextsearch import fulltextsearch

        self.config.registry.settings['default_locale_name'] = 'it'
        request = testing.DummyRequest()
        response = fulltextsearch(request)
        self.assertTrue(isinstance(response, HTTPInternalServerError))

    def test_badrequest_noquery(self):
        from pyramid.httpexceptions import HTTPBadRequest
        from c2cgeoportal.views.fulltextsearch import fulltextsearch

        request = testing.DummyRequest()
        response = fulltextsearch(request)
        self.assertTrue(isinstance(response, HTTPBadRequest))

    def test_badrequest_limit(self):
        from pyramid.httpexceptions import HTTPBadRequest
        from c2cgeoportal.views.fulltextsearch import fulltextsearch

        request = testing.DummyRequest(params=dict(query='text', limit='bad'))
        response = fulltextsearch(request)
        self.assertTrue(isinstance(response, HTTPBadRequest))

    def test_match(self):
        from pyramid.httpexceptions import HTTPBadRequest
        from geojson.feature import FeatureCollection
        from c2cgeoportal.views.fulltextsearch import fulltextsearch

        request = testing.DummyRequest(params=dict(query='tra sol', limit=40))
        resp = fulltextsearch(request)
        self.assertTrue(isinstance(resp, FeatureCollection))
        self.assertEqual(len(resp.features), 1)
        self.assertEqual(resp.features[0].properties['label'], 'label')
        self.assertEqual(resp.features[0].properties['layer_name'], 'layer')

    def test_nomatch(self):
        from pyramid.httpexceptions import HTTPBadRequest
        from geojson.feature import FeatureCollection
        from c2cgeoportal.views.fulltextsearch import fulltextsearch

        request = testing.DummyRequest(params=dict(query='foo'))
        resp = fulltextsearch(request)
        self.assertTrue(isinstance(resp, FeatureCollection))
        self.assertEqual(len(resp.features), 0)
