# Copyright (c) 2011-2024, Camptocamp SA
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
import logging

import transaction

from c2cgeoportal_geoportal.scripts import fill_arguments, get_appsettings, get_session

_LOG = logging.getLogger(__name__)


def main() -> None:
    """Create and populate the database tables."""
    parser = argparse.ArgumentParser(description="Create and populate the database tables.")
    fill_arguments(parser)
    options = parser.parse_args()
    settings = get_appsettings(options)

    with transaction.manager:
        session = get_session(settings, transaction.manager)

        from c2cgeoportal_commons.models.main import (  # pylint: disable=import-outside-toplevel
            Interface,
            LayerGroup,
            LayerWMS,
            OGCServer,
            Theme,
        )

        interfaces = session.query(Interface).all()
        ogc_jpeg = session.query(OGCServer).filter(OGCServer.name == "MapServer_JPEG").one()
        session.delete(ogc_jpeg)

        ogc_server_mapserver = session.query(OGCServer).filter(OGCServer.name == "MapServer").one()

        layer_borders = LayerWMS("Borders", "borders")
        layer_borders.interfaces = interfaces
        layer_borders.ogc_server = ogc_server_mapserver
        layer_density = LayerWMS("Density", "density")
        layer_density.interfaces = interfaces
        layer_density.ogc_server = ogc_server_mapserver

        group_mapserver = LayerGroup("MapServer")
        group_mapserver.children = [layer_borders, layer_density]

        theme = Theme("Demo")
        theme.children = [group_mapserver]
        theme.interfaces = interfaces

        session.add(theme)

        print("Successfully added the demo theme")


if __name__ == "__main__":
    main()
