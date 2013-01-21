# -*- coding: utf-8 -*-
# flake8: noqa

import os
import time
import email
import ConfigParser
from math import ceil
from random import random

from pyramid.wsgi import wsgiapp

# default expiration time is set to 1 week
DEFAULT_EXPIRATION = 3600*24*7

# TileCache Service instance
_service = None

def load_tilecache_config(settings):
    """ Load the TileCache config.

    This function calls ``TileCache.Service.Service.load`` and
    stores the return value in a private global variable.

    Arguments:

    * ``settings``: a dict with a ``tilecache.cfg`` key whose
      value provides the path to TileCache configuratio file.
    """
    from TileCache.Service import Service
    global _service
    _service = Service.load(settings.get('tilecache.cfg'))
    if 'traceback' in _service.metadata:
        print 'Tilecache loading error: '
        print _service.metadata['exception']
        print _service.metadata['traceback']

def createImage(path_info):
    from tileforge import generator

    path = path_info.split('/')
    layername = path[3]
    layer = _service.layers.get(layername)
    z = int(path[7])
    row = int(path[8])
    col = int(path[9].split('.')[0])
    row_count = int(ceil(((layer.bbox[3] - layer.bbox[1]) / layer.size[1]) /
                         layer.resolutions[z]))
    tile = (col, row_count - 1 - row, z)

    generator.init(layer, _service.cache)
    generator.run(tile)

def wsgiHandler(environ, start_response):
    from paste.request import parse_formvars
    from TileCache.Service import TileCacheException
    try:
        path_info = ""

        if "PATH_INFO" in environ: 
            path_info = environ["PATH_INFO"]

        l = len("/tilecache")
        image_file = _service.config.get("cache", "base") + path_info[l:len(path_info)]

        if not os.access(image_file, os.F_OK):
            # 3 trys to create image
            try:
                createImage(path_info)
            except:
                try:
                    # sleep 0..1 segond
                    time.sleep(random())
                    createImage(path_info)
                except:
                    # sleep 0..1 segond
                    time.sleep(random())
                    createImage(path_info)

        if os.access(image_file, os.R_OK):
            if image_file[len(image_file) - 4:len(image_file)] == '.png':
                start_response("200 OK", [('Content-Type','image/png')])
            else:
                start_response("200 OK", [('Content-Type','image/jpeg')])
            return [open(image_file, 'rb').read()]
        else:
            start_response("404 Tile Not Found", [('Content-Type','text/plain')])
            return ["No tile generated"]

    except TileCacheException, E:
        start_response("404 Tile Not Found", [('Content-Type','text/plain')])
        return ["An error occurred: %s" % (str(E))]

@wsgiapp
def tilecache(environ, start_response):
    try:
        expiration = _service.config.getint('cache', 'expire')
    except ConfigParser.NoOptionError:
        expiration = DEFAULT_EXPIRATION

    # custom_start_response adds cache headers to the response
    def custom_start_response(status, headers, exc_info=None):
        headers.append(('Cache-Control', 
                'public, max-age=%s' % expiration))
        headers.append(('Expires', 
                email.Utils.formatdate(time.time() + expiration, 
                False, True)))
        return start_response(status, headers, exc_info)

    return wsgiHandler(environ, custom_start_response)

