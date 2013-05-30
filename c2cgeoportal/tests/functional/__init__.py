# -*- coding: utf-8 -*-

# Copyright (c) 2013, Camptocamp SA
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# The views and conclusions contained in the software and documentation are those
# of the authors and should not be interpreted as representing official policies,
# either expressed or implied, of the FreeBSD Project.


"""Pyramid application test package
"""

import os
from ConfigParser import ConfigParser
from urlparse import urlparse, urljoin

mapserv_url = None
db_url = None

curdir = os.path.dirname(os.path.abspath(__file__))
configfile = os.path.realpath(os.path.join(curdir, 'test.ini'))

if os.path.exists(configfile):
    cfg = ConfigParser()
    cfg.read(configfile)
    db_url = cfg.get('test', 'sqlalchemy.url')
    mapserv_url = urlparse(cfg.get('test', 'mapserv.url'))
    host = mapserv_url.hostname
    mapserv_url = urljoin('http://localhost/', mapserv_url.path)

def setUpCommon():
    import c2cgeoportal
    c2cgeoportal.schema = 'main'
    c2cgeoportal.srid = 21781
    c2cgeoportal.caching.init_region({'backend': 'dogpile.cache.memory'})

    # if test.in does not exist (because the z3c.recipe.filetemplate
    # part hasn't been executed) then db_url is None
    if db_url is None:  # pragma: nocover
        return

    # verify that we have a working database connection before going
    # forward
    from sqlalchemy import create_engine
    from sqlalchemy.exc import OperationalError
    engine = create_engine(db_url)
    try:
        engine.connect()
    except OperationalError:  # pragma: nocover
        return

    import sqlahelper
    sqlahelper.add_engine(engine)

    from c2cgeoportal.models import Base
    Base.metadata.create_all()


def tearDownCommon():

    # if test.in does not exist (because the z3c.recipe.filetemplate
    # part hasn't been executed) then db_url is None
    if db_url is None:  # pragma: nocover
        return

    # verify that we have a working database connection before going
    # forward
    from sqlalchemy import create_engine
    from sqlalchemy.exc import OperationalError
    engine = create_engine(db_url)
    try:
        engine.connect()
    except OperationalError:  # pragma: nocover
        return

    from c2cgeoportal.models import Base
    Base.metadata.drop_all(checkfirst=True)

    import sqlahelper
    sqlahelper.reset()

    from c2cgeoportal import caching
    caching.invalidate_region()
    del caching._regions[None]
