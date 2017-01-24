# -*- coding: utf-8 -*-

# Copyright (c) 2011-2017, Camptocamp SA
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


import argparse
import transaction
from pyramid.paster import get_app, setup_logging


def main():
    parser = argparse.ArgumentParser(
        description="Create and populate the database tables."
    )
    parser.add_argument(
        '-i', '--iniconfig',
        default='production.ini',
        help='project .ini config file'
    )
    parser.add_argument(
        '-n', '--app-name',
        default="app",
        help='The application name (optional, default is "app")'
    )

    options = parser.parse_args()

    # read the configuration
    setup_logging(options.iniconfig)
    get_app(options.iniconfig, options.app_name)

    from c2cgeoportal.models import DBSession, Interface, OGCServer, Theme, LayerGroup, LayerWMS

    session = DBSession()

    interfaces = session.query(Interface).all()
    ogc_server = session.query(OGCServer).filter(OGCServer.name == u"source for image/png").one()

    layer_borders = LayerWMS(u"Borders", u"borders")
    layer_borders.interfaces = interfaces
    layer_borders.ogc_server = ogc_server
    layer_density = LayerWMS(u"Density", u"density")
    layer_density.interfaces = interfaces
    layer_density.ogc_server = ogc_server

    group = LayerGroup(u"Demo")
    group.children = [layer_borders, layer_density]

    theme = Theme(u"Demo")
    theme.children = [group]
    theme.interfaces = interfaces

    transaction.commit()


if __name__ == "__main__":
    main()
