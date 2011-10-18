# -*- coding: utf-8 -*-

import os
import time
import email
import ConfigParser
from math import ceil
from random import random

from pyramid.wsgi import wsgiapp
from TileCache.Service import Service, TileCacheException
from tileforge import generator


# default expiration time is set to 1 year
DEFAULT_EXPIRATION = 3600*24*365

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
    global _service
    _service = Service.load(settings.get('tilecache.cfg'))

def createImage (path_info, service):
    path = path_info.split('/')
    layername = path[3]
    layer = service.layers.get(layername)
    z = int(path[7])
    row = int(path[8])
    col = int(path[9].split('.')[0])
    row_count = int(ceil(((layer.bbox[3] - layer.bbox[1]) / layer.size[1]) /
                         layer.resolutions[z]))
    tile = (col, row_count - 1 - row, z)

    generator.init(layer, service.cache)
    generator.run(tile)

def wsgiHandler (environ, start_response, service):
    from paste.request import parse_formvars
    try:
        path_info = host = ""

        if "PATH_INFO" in environ: 
            path_info = environ["PATH_INFO"]

        l = len("/tilecache")
        image_file = service.config.get("cache", "base") + path_info[l:len(path_info)]

        if not os.access(image_file, os.F_OK):
            # 3 trys to create image
            try:
                createImage(path_info, service)
            except:
                try:
                    # sleep 0..1 segond
                    time.sleep(random())
                    createImage(path_info, service)
                except:
                    # sleep 0..1 segond
                    time.sleep(random())
                    createImage(path_info, service)

        if os.access(image_file, os.R_OK):
            if image_file[len(image_file) - 4:len(image_file)] == '.png':
                start_response("200 OK", [('Content-Type','image/png')])
            else:
                start_response("200 OK", [('Content-Type','image/jpeg')])
            return [open(image_file).read()]
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
        headers.append(('Cache-Control', 'public, max-age=%s'
            % expiration))
        headers.append(('Expires', email.Utils.formatdate(
            time.time() + expiration, False, True)))
        return start_response(status, headers, exc_info)

    return wsgiHandler(environ, custom_start_response, _service)

