# -*- coding: utf-8 -*-


def get_setting(settings, path, default=None):
    value = settings
    for p in path:
        if value and p in value:
            value = value[p]
        else:
            return default
    return value if value else default
