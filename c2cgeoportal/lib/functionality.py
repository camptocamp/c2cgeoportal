# -*- coding: utf-8 -*-

def _get_config_functionalities(name, registered, config):
    functionalities = None

    if registered:
        functionalities = config.get('registered_functionalities')
    if functionalities is None:
        functionalities = config.get('anonymous_functionalities')

    return functionalities.get(name) if functionalities is not None else None


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
