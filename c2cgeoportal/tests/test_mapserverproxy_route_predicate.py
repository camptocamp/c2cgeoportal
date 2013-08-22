# -*- coding: utf-8 -*-

# Copyright (c) 2013, Camptocamp SA
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


def test_hide_capabilities_unset():
    from c2cgeoportal import mapserverproxy_route_predicate
    from pyramid.threadlocal import get_current_registry
    from pyramid.request import Request

    request = Request.blank('/test')
    request.registry = get_current_registry()
    request.registry.settings = {}
    ret = mapserverproxy_route_predicate(None, request)
    assert ret is True


def test_hide_capabilities_set_no_request_param():
    from c2cgeoportal import mapserverproxy_route_predicate
    from pyramid.threadlocal import get_current_registry
    from pyramid.request import Request

    request = Request.blank('/test')
    request.registry = get_current_registry()
    request.registry.settings = {
        'hide_capabilities': True
    }
    ret = mapserverproxy_route_predicate(None, request)
    assert ret is True


def test_hide_capabilities_set_not_get_capabilities_request():
    from c2cgeoportal import mapserverproxy_route_predicate
    from pyramid.threadlocal import get_current_registry
    from pyramid.request import Request

    request = Request.blank('/test?REQUEST=GetMap')
    request.registry = get_current_registry()
    request.registry.settings = {
        'hide_capabilities': True
    }
    ret = mapserverproxy_route_predicate(None, request)
    assert ret is True


def test_hide_capabilities_set_get_capabilities_request():
    from c2cgeoportal import mapserverproxy_route_predicate
    from pyramid.threadlocal import get_current_registry
    from pyramid.request import Request

    request = Request.blank('/test?REQUEST=GetCapabilities')
    request.registry = get_current_registry()
    request.registry.settings = {
        'hide_capabilities': True
    }
    ret = mapserverproxy_route_predicate(None, request)
    assert ret is False
