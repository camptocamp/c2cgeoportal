# -*- coding: utf-8 -*-
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
    else:
        namespace = '%s:%s|%s' % (fn.__module__, fn.__name__, namespace)

    args = inspect.getargspec(fn)
    has_self = args[0] and args[0][0] in ('self', 'cls')

    def generate_key(*args, **kw):
        if kw:
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
    except KeyError:
        raise Exception(
            "No such caching region. A region must be"
            "initialized before it can be used")


def invalidate_region(region=None):
    return get_region(region).invalidate()
