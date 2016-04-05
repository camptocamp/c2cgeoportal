# -*- coding: utf-8 -*-

# Copyright (c) 2014-2016, Camptocamp SA
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


import sys
import transaction
from json import loads
from argparse import ArgumentParser
from pyramid.paster import get_app


def main():
    parser = ArgumentParser(
        prog=sys.argv[0], add_help=True,
        description="Tool used to migrate your old layers from the old structure to the new one.",
    )

    parser.add_argument(
        "-i", "--app-config",
        default="production.ini",
        dest="app_config",
        help="the application .ini config file (optional, default is 'production.ini')"
    )
    parser.add_argument(
        "-n", "--app-name",
        default="app",
        dest="app_name",
        help="the application name (optional, default is 'app')"
    )
    parser.add_argument(
        "--no-layers",
        dest="layers",
        action="store_false",
        help="don't import the layers"
    )
    parser.add_argument(
        "--no-groups",
        dest="groups",
        action="store_false",
        help="don't import the groups"
    )
    options = parser.parse_args()

    app_config = options.app_config
    app_name = options.app_name
    if app_name is None and "#" in app_config:
        app_config, app_name = app_config.split("#", 1)
    get_app(app_config, name=app_name)

    # must be done only once we have loaded the project config
    from c2cgeoportal.models import DBSession, \
        ServerOGC, LayerWMS, LayerWMTS, LayerV1, LayerGroup

    session = DBSession()

    if options.layers:
        table_list = [LayerWMTS, LayerWMS, ServerOGC]
        for table in table_list:
            print("Emptying table %s." % str(table.__table__))
            # must be done exactly this way othewise the cascade config in the
            # models are not used
            for t in session.query(table).all():
                session.delete(t)

        # list and create all distinct server_ogc
        server_ogc(session)

        print("Converting layerv1.")
        for layer in session.query(LayerV1).all():
            layer_v1tov2(session, layer)

    if options.groups:
        print("Converting layer group.")
        for group in session.query(LayerGroup).all():
            layergroup_v1tov2(session, group)

    transaction.commit()


def server_ogc(session):
    from c2cgeoportal.models import LayerV1, ServerOGC

    servers_v1 = session.query(
        LayerV1.url, LayerV1.image_type, LayerV1.is_single_tile).group_by(
            LayerV1.url, LayerV1.image_type, LayerV1.is_single_tile).all()
    unique_servers = []

    # get existing list of server_ogc
    servers_ogc = session.query(ServerOGC).all()
    for server in servers_ogc:
        identifier = str(server.url) + ' ' + str(server.image_type) + ' ' + \
            str(server.is_single_tile)
        if identifier not in unique_servers:
            unique_servers.append(identifier)

    # add new server_ogc
    for server in servers_v1:
        # default image_type
        image_type = server[1]
        if server[1] is None:
            image_type = 'image/png'
        identifier = str(server[0]) + ' ' + image_type + ' ' + str(server[2])
        if identifier not in unique_servers:
            unique_servers.append(identifier)
            new_server_ogc = ServerOGC()
            new_server_ogc.url = server[0]
            new_server_ogc.image_type = image_type
            new_server_ogc.is_single_tile = server[2]
            name = server[0]
            if name is None:
                name = str(server[1])
            if server[2]:
                name += ' with single_tile'
            new_server_ogc.name = u'source for %s' % name

            session.add(new_server_ogc)

    transaction.commit()


def layer_v1tov2(session, layer):
    from c2cgeoportal.models import ServerOGC, LayerWMS, LayerWMTS, \
        LayergroupTreeitem, WMTSDimension

    if layer.layer_type == "internal WMS" or layer.layer_type == "external WMS":
        # use the first one
        new_layer = LayerWMS()
        image_type = layer.image_type
        if layer.image_type is None:
            image_type = 'image/png'
        server_ogc = session.query(ServerOGC).filter(
            ServerOGC.url == layer.url,
            ServerOGC.image_type == image_type, ServerOGC.is_single_tile ==
            layer.is_single_tile).one()
        new_layer.server_ogc = server_ogc
    elif layer.layer_type == "WMTS":
        new_layer = LayerWMTS()

    new_layer.name = layer.name
    new_layer.public = layer.public
    new_layer.geo_table = layer.geo_table
    new_layer.interfaces = layer.interfaces

    for link in layer.parents_relation:
        new_link = LayergroupTreeitem()
        new_link.ordering = link.ordering
        new_link.treegroup_id = link.treegroup_id
        new_link.group = link.group
        new_link.item = new_layer

    if layer.layer_type[-4:] == " WMS":
        new_layer.layer = layer.name
        new_layer.style = layer.style
        new_layer.time_mode = layer.time_mode
        new_layer.time_widget = layer.time_widget

    if layer.layer_type == "WMTS":
        new_layer.url = layer.url
        new_layer.layer = layer.name
        new_layer.style = layer.style
        new_layer.matrix_set = layer.matrix_set
        new_layer.image_type = layer.image_type

        if layer.dimensions is not None:
            dimensions = loads(layer.dimensions)
            for name, value in dimensions.items():
                session.add(WMTSDimension(name, value, new_layer))

    layer_add_ui_metadata(layer, new_layer, session)

    session.add(new_layer)


def new_uimetadata(name, value, item):
    from c2cgeoportal.models import UIMetadata

    uimetadata = UIMetadata(name, value)
    uimetadata.item = item
    return uimetadata


def layer_add_ui_metadata(layer, new_layer, session):
    if layer.metadata_url is not None:
        session.add(new_uimetadata(u"metadataUrl", layer.metadata_url, new_layer))
    if layer.is_checked is True:
        session.add(new_uimetadata(u"isChecked", u"true", new_layer))
    if layer.icon is not None:
        session.add(new_uimetadata(u"icon", layer.icon, new_layer))
    if layer.wms_url is not None:
        session.add(new_uimetadata(u"wmsUrl", layer.wms_url, new_layer))
    if layer.wms_layers is not None:
        session.add(new_uimetadata(u"wmsLayers", layer.wms_layers, new_layer))
    if layer.query_layers is not None:
        session.add(new_uimetadata(u"queryLayers", layer.query_layers, new_layer))
    if layer.legend is not None:
        session.add(new_uimetadata(u"legend", layer.legend, new_layer))
    if layer.legend_image is not None:
        session.add(new_uimetadata(u"legendImage", layer.legend_image, new_layer))
    if layer.legend_rule is not None:
        session.add(new_uimetadata(u"legendRule", layer.legend_rule, new_layer))
    if layer.is_legend_expanded is True:
        session.add(new_uimetadata(u"isLegendExpanded", u"true", new_layer))
    if layer.min_resolution is not None:
        session.add(new_uimetadata(u"minResolution", layer.min_resolution, new_layer))
    if layer.max_resolution is not None:
        session.add(new_uimetadata(u"maxResolution", layer.max_resolution, new_layer))
    if layer.disclaimer is not None:
        session.add(new_uimetadata(u"disclaimer", layer.disclaimer, new_layer))
    if layer.identifier_attribute_field is not None:
        session.add(new_uimetadata(
            u"identifier_attribute_field",
            layer.identifier_attribute_field, new_layer
        ))
    if layer.exclude_properties is not None:
        session.add(new_uimetadata("excludeProperties", layer.exclude_properties, new_layer))


def layergroup_v1tov2(session, group):
    is_expended_metadatas = group.get_metadatas("isExpanded")
    if group.is_expanded is True:
        if len(is_expended_metadatas) > 0:
            is_expended_metadatas[0].value = u"true"
        else:
            session.add(new_uimetadata(u"isExpanded", u"true", group))
    elif len(is_expended_metadatas) > 0:
        session.delete(is_expended_metadatas)
