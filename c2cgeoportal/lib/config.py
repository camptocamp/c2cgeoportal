# -*- coding: utf-8 -*-

import simplejson as json


def cleanup_json(value):
    start = value.index('{')
    end = value.rindex('}')
    result = value[start:end + 1]
    return json.loads(result.replace('\\n', '\n'))
