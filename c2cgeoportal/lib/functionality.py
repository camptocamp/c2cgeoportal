# -*- coding: utf-8 -*-

from c2cgeoportal.lib import get_setting


def _get_config_functionality(name, registered, config):
    result = None

    if registered:
        result = get_setting(
            config, ('functionalities', 'registered', name))
    if result is None:
        result = get_setting(
            config, ('functionalities', 'anonymous', name))

    if result is None:
        result = []
    elif not isinstance(result, list):
        result = [result]

    return result


def _get_db_functionality(name, user):
    result = [
        functionality.value for
        functionality in user.functionalities
        if functionality.name == name]
    if len(result) == 0:
        result = [
            functionality.value for
            functionality in user.role.functionalities
            if functionality.name == name]
    return result


def get_functionality(name, config, request):
    result = []
    if request.user:
        result = _get_db_functionality(name, request.user)
    if len(result) == 0:
        result = _get_config_functionality(name, request.user is not None, config)
    return result
