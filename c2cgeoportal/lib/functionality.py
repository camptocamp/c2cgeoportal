# -*- coding: utf-8 -*-

from c2cgeoportal.lib.config import cleanup_json


def _get_json_functionalities(value, name, config):
    obj = cleanup_json(config[value])
    return obj[name] if name in obj else None


def _get_config_functionalities(name, registered, config):
    result = _get_json_functionalities('registered_functionalities',
            name, config)
    return result if result != None and registered \
        else _get_json_functionalities('anonymous_functionalities',
            name, config)


def _get_db_functionalities(name, request):
    user = request.user
    result = []
    if user:
        result = [functionality.value for functionality in user.functionalities if functionality.name == name]
        if len(result) == 0:
            result = [functionality.value for functionality in user.role.functionalities if functionality.name == name]
    return (result, user != None)


def get_functionality(name, config, request, default=None):
    result, registred = _get_db_functionalities(name, request)
    if len(result) == 0:
        return _get_config_functionalities(name, registred, config) or default
    else:
        return result[0]


def get_functionalities(name, config, request, default=[]):
    result, registred = _get_db_functionalities(name, request)
    if len(result) == 0:
        return _get_config_functionalities(name, registred, config) or default
    else:
        return result
