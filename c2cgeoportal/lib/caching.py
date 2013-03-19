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


import inspect

from dogpile.cache import compat
from dogpile.cache.region import make_region

_regions = {}


def keygen_function(namespace, fn):
    """Return a function that generates a string
    key, based on a given function as well as
    arguments to the returned function itself.

    This is used by :meth:`.CacheRegion.cache_on_arguments`
    to generate a cache key from a decorated function.
    """

    if namespace is None:
        namespace = '%s:%s' % (fn.__module__, fn.__name__)
    else:  # pragma: nocover
        namespace = '%s:%s|%s' % (fn.__module__, fn.__name__, namespace)

    args = inspect.getargspec(fn)
    has_self = args[0] and args[0][0] in ('self', 'cls')

    def generate_key(*args, **kw):
        if kw:  # pragma: nocover
            raise ValueError(
                "key creation function does not accept keyword arguments.")
        parts = [namespace]
        if has_self:
            self_ = args[0]
            if hasattr(self_, 'request'):
                parts.append(self_.request.application_url)
            args = args[1:]
        parts.append(" ".join(map(compat.text_type, args)))
        return "|".join(parts)
    return generate_key


def init_region(conf, region=None):
    """
    Initialize the caching module.
    """
    cache_region = make_region(function_key_generator=keygen_function)
    kwargs = dict(
        (k, conf[k]) for k in
        ('arguments', 'expiration_time') if k in conf)
    cache_region.configure(conf['backend'], **kwargs)
    _regions[region] = cache_region
    return cache_region


def get_region(region=None):
    """
    Return a cache region.
    """
    try:
        return _regions[region]
    except KeyError:  # pragma: nocover
        raise Exception(
            "No such caching region. A region must be"
            "initialized before it can be used")


def invalidate_region(region=None):
    return get_region(region).invalidate()
