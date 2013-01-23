# -*- coding: utf-8 -*-

# Copyright (c) 2012-2013 by Camptocamp SA


from unittest import TestCase

class TestWFSParsing(TestCase):
    def test_is_get_feature(self):
        from c2cgeoportal.lib.wfsparsing import is_get_feature
        from c2cgeoportal.tests.xmlstr import getfeature
        assert is_get_feature(getfeature)

    def test_is_get_feature_not(self):
        from c2cgeoportal.lib.wfsparsing import is_get_feature
        assert not is_get_feature('<is_not>foo</is_not>')

    def test_limit_featurecollection_outlimit(self):
        from xml.etree.ElementTree import fromstring
        from c2cgeoportal.lib.wfsparsing import limit_featurecollection
        from c2cgeoportal.tests.xmlstr import featurecollection_outlimit
        content = limit_featurecollection(featurecollection_outlimit)
        collection = fromstring(content.encode('utf-8'))
        features = collection.findall(
                '{http://www.opengis.net/gml}featureMember') 
        self.assertEquals(len(features), 200)

        from xml.etree.ElementTree import fromstring
        from c2cgeoportal.lib.wfsparsing import limit_featurecollection
        from c2cgeoportal.tests.xmlstr import featurecollection_outlimit
        content = limit_featurecollection(featurecollection_outlimit, limit=2)
        collection = fromstring(content.encode('utf-8'))
        features = collection.findall(
                '{http://www.opengis.net/gml}featureMember') 
        self.assertEquals(len(features), 2)

    def test_limit_featurecollection_inlimit(self):
        from xml.etree.ElementTree import fromstring
        from c2cgeoportal.lib.wfsparsing import limit_featurecollection
        from c2cgeoportal.tests.xmlstr import featurecollection_inlimit
        content = limit_featurecollection(featurecollection_inlimit)
        collection = fromstring(content.encode('utf-8'))
        features = collection.findall(
                '{http://www.opengis.net/gml}featureMember') 
        self.assertEquals(len(features), 199)
