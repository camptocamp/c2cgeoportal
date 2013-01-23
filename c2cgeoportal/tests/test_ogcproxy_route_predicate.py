# -*- coding: utf-8 -*-

# Copyright (c) 2012-2013 by Camptocamp SA


def test_no_url():
    from c2cgeoportal import ogcproxy_route_predicate
    from pyramid.request import Request

    request = Request.blank('/test')
    ret = ogcproxy_route_predicate(None, request)
    assert ret == False


def test_mapserv_url():
    from c2cgeoportal import ogcproxy_route_predicate
    from pyramid.request import Request

    request = Request.blank('/test?url=http://foo.com/mapserv')
    ret = ogcproxy_route_predicate(None, request)
    assert ret == False


def test_non_mapserv_url():
    from c2cgeoportal import ogcproxy_route_predicate
    from pyramid.request import Request

    request = Request.blank('/test?url=http://foo.com/wmts')
    ret = ogcproxy_route_predicate(None, request)
    assert ret == True
