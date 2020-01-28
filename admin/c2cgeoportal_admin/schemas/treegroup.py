# -*- coding: utf-8 -*-

# Copyright (c) 2018-2020, Camptocamp SA
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


from functools import partial

from c2cgeoform.schema import GeoFormSchemaNode
import colander
from sqlalchemy.orm import aliased
from sqlalchemy.sql.expression import case, func

from c2cgeoportal_admin import _
from c2cgeoportal_admin.widgets import ChildrenWidget, ChildWidget
from c2cgeoportal_commons.models.main import LayergroupTreeitem, TreeItem


class ChildSchemaNode(GeoFormSchemaNode):  # pylint: disable=abstract-method
    def objectify(self, dict_, context=None):
        if dict_.get("id", None):
            context = self.dbsession.query(LayergroupTreeitem).get(dict_["id"])
        context = super().objectify(dict_, context)
        context.treeitem = self.dbsession.query(TreeItem).get(dict_["treeitem_id"])
        return context


def treeitems(node, kw, only_groups=False):  # pylint: disable=unused-argument
    dbsession = kw["request"].dbsession

    group = case([(func.count(LayergroupTreeitem.id) == 0, "Unlinked")], else_="Others").label("group")

    query = (
        dbsession.query(TreeItem, group)
        .distinct()
        .outerjoin("parents_relation")
        .filter(TreeItem.item_type != "theme")
        .group_by(TreeItem.id)
        .order_by(group.desc(), TreeItem.name)
    )

    # Do not propose ancestors to avoid cycles
    item_id = kw["request"].matchdict["id"]
    if item_id != "new":
        search_ancestors = (
            dbsession.query(LayergroupTreeitem.treegroup_id)
            .filter(LayergroupTreeitem.treeitem_id == item_id)
            .cte(name="ancestors", recursive=True)
        )
        search_alias = aliased(search_ancestors, name="search_ancestors")
        relation_alias = aliased(LayergroupTreeitem, name="relation")
        search_ancestors = search_ancestors.union_all(
            dbsession.query(relation_alias.treegroup_id).filter(
                relation_alias.treeitem_id == search_alias.c.treegroup_id
            )
        )
        ancestors = dbsession.query(search_ancestors.c.treegroup_id).subquery("ancestors")

        query = query.filter(~TreeItem.id.in_(ancestors)).filter(TreeItem.id != item_id)

    if only_groups:
        query = query.filter(TreeItem.item_type == "group")

    return query


def children_validator(node, cstruct):
    for dict_ in cstruct:
        if not dict_["treeitem_id"] in [item.id for item, group in node.treeitems]:
            raise colander.Invalid(
                node,
                _("Value {} does not exist in table {} or is not allowed to avoid cycles").format(
                    dict_["treeitem_id"], TreeItem.__tablename__
                ),
            )


def base_deferred_parent_id_validator(node, kw, model):  # pylint: disable=unused-argument
    def validator(node, cstruct):
        if kw["dbsession"].query(model).filter(model.id == cstruct).count() == 0:
            raise colander.Invalid(
                node, "Value {} does not exist in table {}".format(cstruct, model.__tablename__)
            )

    return validator


def children_schema_node(only_groups=False):
    return colander.SequenceSchema(
        ChildSchemaNode(LayergroupTreeitem, name="layergroup_treeitem", widget=ChildWidget()),
        name="children_relation",
        title=_("Children"),
        treeitems=colander.deferred(partial(treeitems, only_groups=only_groups)),
        validator=children_validator,
        widget=ChildrenWidget(category="structural"),
    )
