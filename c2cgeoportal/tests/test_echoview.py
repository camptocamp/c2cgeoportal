# -*- coding: utf-8 -*-

# Copyright (c) 2012-2013 by Camptocamp SA


def test_json_base64_encode():
    import StringIO
    from c2cgeoportal.views.echo import json_base64_encode

    sio = StringIO.StringIO()
    sio.write('some content with non-ASCII chars ç à é')
    sio.flush()
    sio.seek(0)

    a = [s for s in json_base64_encode('a file name', sio)]
    s = ''.join(a)

    assert s == '{"filename":"a file name","data":"c29tZSBjb250ZW50IHdpdGggbm9uLUFTQ0lJIGNoYXJzIMOnIMOgIMOp","success":true}'
