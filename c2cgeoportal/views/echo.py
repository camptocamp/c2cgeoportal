from base64 import b64encode
import os.path
import re

from pyramid.httpexceptions import HTTPBadRequest
from pyramid.response import Response
from pyramid.view import view_config


def base64_encode_chunks(file, chunk_size=57):
    """
    Generate base64 encoded lines of up to 76 (== 57 * 8 / 6) characters, according to RFC2045.
    See http://en.wikipedia.org/wiki/Base64
    """
    while True:
        line = file.read(chunk_size)
        if not line:
            break
        yield b64encode(line) + '\n'


@view_config(route_name='echo')
def echo(request):
    """
    Echo an uploaded file back to the client as an text/html document so it can be handled by Ext.
    The response is base64 encoded to ensure that there are no special HTML characters or charset problems.
    See http://docs.sencha.com/ext-js/3-4/#!/api/Ext.form.BasicForm-cfg-fileUpload
    """
    if request.method != 'POST':
        raise HTTPBadRequest()
    try:
        file = request.POST['file']
    except KeyError:
        raise HTTPBadRequest()
    response = Response()
    response.app_iter = base64_encode_chunks(file.file)
    response.content_type = 'text/html'
    return response
