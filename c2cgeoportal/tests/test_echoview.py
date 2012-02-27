# -*- coding: utf-8 -*-

def test_json_base64_encode_chunks():
    import StringIO
    from c2cgeoportal.views.echo import json_base64_encode_chunks

    sio = StringIO.StringIO()
    sio.write('some content with non-ASCII chars ç à é')
    sio.flush()
    sio.seek(0)

    a = [s for s in json_base64_encode_chunks('a file name', sio)]
    s = ''.join(a)

    assert s == '{"filename":"a file name","data":"c29tZSBjb250ZW50IHdpdGggbm9uLUFTQ0lJIGNoYXJzIMOnIMOgIMOp","success":true}'
