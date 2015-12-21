# -*- coding: utf-8 -*-

# Copyright (c) 2013-2015, Camptocamp SA
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


from nose.plugins.attrib import attr
from unittest import TestCase

from c2cgeoportal.tests.functional import (  # noqa
    tear_down_common as tearDownModule,
    set_up_common as setUpModule,
    create_dummy_request
)


@attr(functional=True)
class TestGeometryProcessing(TestCase):

    def test_difference(self):
        from shapely.geometry import Polygon
        from c2cgeoportal.views.geometry_processing import GeometryProcessing

        request = create_dummy_request()
        request.method = "POST"
        request.body = '{ "geometries": [{ "type": "Polygon", "coordinates": [[[0, 0], [0, 4], [4, 4], [4, 0], [0, 0]]] }, ' \
            '{ "type": "Polygon", "coordinates": [[[2, 1], [2, 3], [6, 3], [6, 1], [2, 1]]] }]}'
        geom_ops = GeometryProcessing(request)
        geom = geom_ops.difference()
        self.assertEquals(
            geom,
            Polygon([(0, 0), (0, 4), (4, 4), (4, 3), (2, 3), (2, 1), (4, 1), (4, 0), (0, 0)])
        )
