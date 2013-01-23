# -*- coding: utf-8 -*-

# Copyright (c) 2012-2013 by Camptocamp SA


def get_setting(settings, path, default=None):
    value = settings
    for p in path:
        if value and p in value:
            value = value[p]
        else:
            return default
    return value if value else default
