# -*- coding: utf-8 -*-

# Copyright (c) 2013-2014, Camptocamp SA
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
            '{http://www.opengis.net/gml}featureMember'
        )
        self.assertEquals(len(features), 200)

        from xml.etree.ElementTree import fromstring
        from c2cgeoportal.lib.wfsparsing import limit_featurecollection
        from c2cgeoportal.tests.xmlstr import featurecollection_outlimit
        content = limit_featurecollection(featurecollection_outlimit, limit=2)
        collection = fromstring(content.encode('utf-8'))
        features = collection.findall(
            '{http://www.opengis.net/gml}featureMember'
        )
        self.assertEquals(len(features), 2)

    def test_limit_featurecollection_inlimit(self):
        from xml.etree.ElementTree import fromstring
        from c2cgeoportal.lib.wfsparsing import limit_featurecollection
        from c2cgeoportal.tests.xmlstr import featurecollection_inlimit
        content = limit_featurecollection(featurecollection_inlimit)
        collection = fromstring(content.encode('utf-8'))
        features = collection.findall(
            '{http://www.opengis.net/gml}featureMember'
        )
        self.assertEquals(len(features), 199)
