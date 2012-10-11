# -*- coding: utf-8 -*-
from dogpile.cache.region import make_region

_regions = {}


def init_region(conf, region=None):
    """
    Initialize the caching module.
    """
    cache_region = make_region()
    kwargs = dict((k, conf[k])
            for k in ('arguments', 'expiration_time') if k in conf)
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
        raise Exception("No such caching region. A region must be"
                "initialized before it can be used")


def invalidate_region(region=None):
    return get_region(region).invalidate()
