# -*- coding: utf-8 -*-

# Copyright (c) 2014-2019, Camptocamp SA
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

"""create database

Revision ID: 166ff2dcc48d
Revises:
Create Date: 2014-10-24 11:43:23.886123
"""

from hashlib import sha1

from alembic import op
from c2c.template.config import config
from sqlalchemy import Column, ForeignKey, MetaData, Table
from sqlalchemy.types import Boolean, DateTime, Float, Integer, String, Unicode, UserDefinedType

# revision identifiers, used by Alembic.
revision = "166ff2dcc48d"
down_revision = None


class TsVector(UserDefinedType):
    """ A custom type for PostgreSQL's tsvector type. """

    def get_col_spec(self):
        return "TSVECTOR"


def upgrade():
    schema = config["schema"]
    schema_static = config["schema_static"]
    parentschema = config.get("parentschema")
    srid = config.get("srid")

    engine = op.get_bind().engine
    if type(engine).__name__ != "MockConnection" and op.get_context().dialect.has_table(
        engine, "functionality", schema=schema
    ):  # pragma: no cover
        return

    op.create_table(
        "functionality",
        Column("id", Integer, primary_key=True),
        Column("name", Unicode, nullable=False),
        Column("value", Unicode, nullable=False),
        Column("description", Unicode),
        schema=schema,
    )
    op.create_table(
        "treeitem",
        Column("type", String(10), nullable=False),
        Column("id", Integer, primary_key=True),
        Column("name", Unicode),
        Column("order", Integer, nullable=False),
        Column("metadataURL", Unicode),
        schema=schema,
    )
    op.create_table(
        "restrictionarea",
        Column("id", Integer, primary_key=True),
        Column("name", Unicode),
        Column("description", Unicode),
        Column("readwrite", Boolean, default=False),
        schema=schema,
    )
    op.execute(
        "SELECT AddGeometryColumn('%(schema)s', 'restrictionarea', "
        "'area', %(srid)s, 'POLYGON', 2)" % {"schema": schema, "srid": srid}
    )
    op.create_table(
        "shorturl",
        Column("id", Integer, primary_key=True),
        Column("url", Unicode(1000)),
        Column("ref", String(20), index=True, unique=True, nullable=False),
        Column("creator_email", Unicode(200)),
        Column("creation", DateTime),
        Column("last_hit", DateTime),
        Column("nb_hits", Integer),
        schema=schema_static,
    )

    op.create_table(
        "role",
        Column("id", Integer, primary_key=True),
        Column("name", Unicode, unique=True, nullable=False),
        Column("description", Unicode),
        schema=schema,
    )
    op.execute(
        "SELECT AddGeometryColumn('%(schema)s', 'role', "
        "'extent', %(srid)s, 'POLYGON', 2)" % {"schema": schema, "srid": srid}
    )
    role = Table("role", MetaData(), Column("name", Unicode, unique=True, nullable=False), schema=schema)
    op.bulk_insert(role, [{"name": "role_admin"}])

    op.create_table(
        "layer",
        Column("id", Integer, ForeignKey(schema + ".treeitem.id"), primary_key=True),
        Column("public", Boolean, default=True),
        Column("inMobileViewer", Boolean, default=True),
        Column("inDesktopViewer", Boolean, default=True),
        Column("isChecked", Boolean, default=True),
        Column("icon", Unicode),
        Column("layerType", Unicode(12)),
        Column("url", Unicode),
        Column("imageType", Unicode(10)),
        Column("style", Unicode),
        Column("dimensions", Unicode),
        Column("matrixSet", Unicode),
        Column("wmsUrl", Unicode),
        Column("wmsLayers", Unicode),
        Column("queryLayers", Unicode),
        Column("kml", Unicode),
        Column("isSingleTile", Boolean),
        Column("legend", Boolean, default=True),
        Column("legendImage", Unicode),
        Column("legendRule", Unicode),
        Column("isLegendExpanded", Boolean, default=False),
        Column("minResolution", Float),
        Column("maxResolution", Float),
        Column("disclaimer", Unicode),
        Column("identifierAttributeField", Unicode),
        Column("geoTable", Unicode),
        Column("excludeProperties", Unicode),
        Column("timeMode", Unicode(8)),
        schema=schema,
    )
    op.create_table(
        "role_restrictionarea",
        Column("role_id", Integer, ForeignKey(schema + ".role.id"), primary_key=True),
        Column("restrictionarea_id", Integer, ForeignKey(schema + ".restrictionarea.id"), primary_key=True),
        schema=schema,
    )
    op.create_table(
        "tsearch",
        Column("id", Integer, primary_key=True),
        Column("label", Unicode),
        Column("layer_name", Unicode),
        Column("role_id", Integer, ForeignKey(schema + ".role.id"), nullable=True),
        Column("public", Boolean, server_default="true"),
        Column("ts", TsVector),
        Column("params", Unicode, nullable=True),
        schema=schema,
    )
    op.execute(
        "SELECT AddGeometryColumn('%(schema)s', 'tsearch', 'the_geom', "
        "%(srid)s, 'GEOMETRY', 2)" % {"schema": schema, "srid": srid}
    )
    op.create_index("tsearch_ts_idx", "tsearch", ["ts"], schema=schema, postgresql_using="gin")
    op.create_table(
        "treegroup",
        Column("id", Integer, ForeignKey(schema + ".treeitem.id"), primary_key=True),
        schema=schema,
    )

    op.create_table(
        "user",
        Column("type", String(10), nullable=False),
        Column("id", Integer, primary_key=True),
        Column("username", Unicode, unique=True, nullable=False),
        Column("password", Unicode, nullable=False),
        Column("email", Unicode, nullable=False),
        Column("is_password_changed", Boolean, default=False),
        Column("role_id", Integer, ForeignKey(schema + ".role.id"), nullable=False),
        schema=schema,
    )
    if parentschema is not None and parentschema != "":  # pragma: no cover
        op.add_column(
            "user", Column("parent_role_id", Integer, ForeignKey(parentschema + ".role.id")), schema=schema
        )
    op.execute(
        "INSERT INTO %(schema)s.user (type, username, email, password, role_id) "
        "(SELECT 'user', 'admin', 'info@example.com', '%(pass)s', r.id "
        "FROM %(schema)s.role AS r "
        "WHERE r.name = 'role_admin')" % {"schema": schema, "pass": sha1("admin".encode("utf-8")).hexdigest()}
    )

    op.create_table(
        "role_functionality",
        Column("role_id", Integer, ForeignKey(schema + ".role.id"), primary_key=True),
        Column("functionality_id", Integer, ForeignKey(schema + ".functionality.id"), primary_key=True),
        schema=schema,
    )
    op.create_table(
        "user_functionality",
        Column("user_id", Integer, ForeignKey(schema + ".user.id"), primary_key=True),
        Column("functionality_id", Integer, ForeignKey(schema + ".functionality.id"), primary_key=True),
        schema=schema,
    )
    op.create_table(
        "layergroup",
        Column("id", Integer, ForeignKey(schema + ".treegroup.id"), primary_key=True),
        Column("isExpanded", Boolean),
        Column("isInternalWMS", Boolean),
        # children have radio button instance of check box
        Column("isBaseLayer", Boolean),
        schema=schema,
    )
    op.create_table(
        "layer_restrictionarea",
        Column("layer_id", Integer, ForeignKey(schema + ".layer.id"), primary_key=True),
        Column("restrictionarea_id", Integer, ForeignKey(schema + ".restrictionarea.id"), primary_key=True),
        schema=schema,
    )
    op.create_table(
        "layergroup_treeitem",
        Column("treegroup_id", Integer, ForeignKey(schema + ".treegroup.id"), primary_key=True),
        Column("treeitem_id", Integer, ForeignKey(schema + ".treeitem.id"), primary_key=True),
        schema=schema,
    )
    op.create_table(
        "theme",
        Column("id", Integer, ForeignKey(schema + ".treegroup.id"), primary_key=True),
        Column("icon", Unicode),
        Column("inMobileViewer", Boolean, default=False),
        Column("inDesktopViewer", Boolean, default=True),
        schema=schema,
    )
    op.create_table(
        "theme_functionality",
        Column("theme_id", Integer, ForeignKey(schema + ".theme.id"), primary_key=True),
        Column("functionality_id", Integer, ForeignKey(schema + ".functionality.id"), primary_key=True),
        schema=schema,
    )

    op.execute(
        'INSERT INTO {schema}.treeitem (type, name, "order") '
        "VALUES ('group', 'background', 0)".format(schema=schema)
    )
    op.execute(
        "INSERT INTO {schema}.treegroup (id) SELECT id " "FROM {schema}.treeitem".format(schema=schema)
    )
    op.execute(
        "INSERT INTO {schema}.layergroup (id) SELECT id " "FROM {schema}.treeitem".format(schema=schema)
    )


def downgrade():
    schema = config["schema"]
    schema_static = config["schema_static"]

    op.drop_table("theme_functionality", schema=schema)
    op.drop_table("theme", schema=schema)
    op.drop_table("layergroup_treeitem", schema=schema)
    op.drop_table("layer_restrictionarea", schema=schema)
    op.drop_table("layergroup", schema=schema)
    op.drop_table("user_functionality", schema=schema)
    op.drop_table("role_functionality", schema=schema)
    op.drop_table("user", schema=schema)
    op.drop_table("treegroup", schema=schema)
    op.drop_table("tsearch", schema=schema)
    op.drop_table("role_restrictionarea", schema=schema)
    op.drop_table("layer", schema=schema)
    op.drop_table("role", schema=schema)
    op.drop_table("shorturl", schema=schema_static)
    op.drop_table("restrictionarea", schema=schema)
    op.drop_table("treeitem", schema=schema)
    op.drop_table("functionality", schema=schema)
