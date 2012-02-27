from base64 import b64encode
import json

from pyramid.httpexceptions import HTTPBadRequest
from pyramid.response import Response
from pyramid.view import view_config


def json_base64_encode_chunks(filename, file, chunk_size=65536):
    """
    Generate a JSON-wrapped base64-encoded string.
    See http://en.wikipedia.org/wiki/Base64
    """
    yield '{"filename":%s,"data":"' % (json.dumps(filename),)
    while True:
        line = file.read(chunk_size)
        if not line:
            break
        yield b64encode(line)
    yield '","success":true}'


@view_config(route_name='echo')
def echo(request):
    """
    Echo an uploaded file back to the client as an text/html document so it can
    be handled by Ext.

    The response is JSON-wrapped and base64-encoded to ensure that there are no
    special HTML characters or charset problems and so that braindead ext
    doesn't barf on it.

    We use an iterator to avoid loading the whole file into memory.  See
    http://docs.sencha.com/ext-js/3-4/#!/api/Ext.form.BasicForm-cfg-fileUpload
    """
    if request.method != 'POST':
        return HTTPBadRequest()
    try:
        file = request.POST['file']
    except KeyError:
        return HTTPBadRequest()
    response = Response()
    response.app_iter = json_base64_encode_chunks(file.filename, file.file)
    response.content_type = 'text/html'
    return response
