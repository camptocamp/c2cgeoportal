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


import logging
import os

from fanstatic import Library, Group, Resource
from fanstatic.core import set_resource_file_existence_checking
from pyramid_formalchemy.utils import TemplateEngine
from formalchemy import config as fa_config
from formalchemy import FieldSet, Grid, helpers
from formalchemy.fields import Field, FieldRenderer, CheckBoxSet, \
    SelectFieldRenderer, AttributeField
from formalchemy.validators import ValidationError
from formalchemy.helpers import password_field
from geoalchemy2 import Geometry
from mako.lookup import TemplateLookup
from fa.jquery import renderers as fa_renderers
from fa.jquery import fanstatic_resources
from pyramid_formalchemy import events as fa_events
from geoformalchemy.base import GeometryFieldRenderer
from pyramid.i18n import TranslationStringFactory
from sqlalchemy.orm.attributes import manager_of_class

from c2cgeoportal import models
from c2cgeoportal import (
    formalchemy_default_zoom,
    formalchemy_default_x, formalchemy_default_y,
    formalchemy_available_functionalities,
    formalchemy_available_metadata,
)

__all__ = [
    "Functionality", "User", "Role", "LayerGroup", "Theme",
    "LayerV1", "OGCServer", "LayerWMS",
    "LayerWMTS", "RestrictionArea", "Interface", "Metadata",
    "Dimension", "LayerV1Grid", "LayerGroupGrid", "ThemeGrid",
    "LayerWMTSGrid", "FunctionalityGrid", "RestrictionAreaGrid", "RoleGrid",
    "UserGrid", "InterfaceGrid", "MetadataGrid", "DimensionGrid"
]


log = logging.getLogger(__name__)
_ = TranslationStringFactory("c2cgeoportal")

fa_config.encoding = "utf-8"
fa_config.engine = TemplateEngine()

fanstatic_lib = Library("admin", "static")
admin_js = Resource(
    fanstatic_lib,
    "build/admin/admin.js",
    depends=[fanstatic_resources.jqueryui])
admin_css = Resource(
    fanstatic_lib,
    "build/admin/admin.css",
    depends=[fanstatic_resources.fa_uiadmin_css])

# HACK to invoke fanstatic to inject a script which content is dynamic:
# the content of the script sets OpenLayers.ImgPath to an url that is
# dynamically generated using request.static_url
olimgpath_js = None
# deactive resource checking in fanstatic
set_resource_file_existence_checking(False)


def get_fanstatic_resources(request):  # pragma: no cover
    global olimgpath_js
    olimgpath = request.static_url("c2cgeoportal:static/lib/openlayers/img/")

    def olimgpath_renderer(url):
        return u'<script>OpenLayers.ImgPath="{0!s}";</script>'.format(olimgpath)
    if olimgpath_js is None:
        olimgpath_js = Resource(
            fanstatic_lib,
            "whatever.js",
            renderer=olimgpath_renderer,
            depends=[admin_js])

    return Group([admin_js, olimgpath_js, admin_css])
# end of HACK


@fa_events.subscriber([models.Functionality, fa_events.IBeforeRenderEvent])
def before_render_functionnality(context, event):  # pragma: no cover
    get_fanstatic_resources(event.request).need()


@fa_events.subscriber([models.Theme, fa_events.IBeforeRenderEvent])
def before_render_theme(context, event):  # pragma: no cover
    get_fanstatic_resources(event.request).need()


@fa_events.subscriber([models.Layer, fa_events.IBeforeRenderEvent])
def before_render_layer(context, event):  # pragma: no cover
    get_fanstatic_resources(event.request).need()


@fa_events.subscriber([models.LayerGroup, fa_events.IBeforeRenderEvent])
def before_render_layergroup(context, event):  # pragma: no cover
    get_fanstatic_resources(event.request).need()


@fa_events.subscriber([models.RestrictionArea, fa_events.IBeforeRenderEvent])
def before_render_restrictionarea(context, event):  # pragma: no cover
    get_fanstatic_resources(event.request).need()


@fa_events.subscriber([models.Role, fa_events.IBeforeRenderEvent])
def before_render_role(context, event):  # pragma: no cover
    get_fanstatic_resources(event.request).need()


@fa_events.subscriber([models.User, fa_events.IBeforeRenderEvent])
def before_render_user(context, event):  # pragma: no cover
    get_fanstatic_resources(event.request).need()


# validator to check uniqueness of unique key in db (prevent duplicate key error)
def unique_validator(value, f):  # pragma: no cover
    query = f.query(f.model.__class__)
    query = query.filter_by(**{f.name: f.value})
    if f.parent._bound_pk is None and query.first():
        raise ValidationError(_(u"Duplicate record"))


class PyramidGeometryFieldRenderer(GeometryFieldRenderer):  # pragma: no cover
    def __init__(self, field):
        self.__templates = None
        GeometryFieldRenderer.__init__(self, field)

    def get_templates(self):
        if self.__templates is None:
            self.__templates = TemplateLookup(
                [os.path.join(os.path.dirname(__file__), "templates", "admin")],
                input_encoding="utf-8", output_encoding="utf-8")
        return self.__templates


FieldSet.default_renderers.update(fa_renderers.default_renderers)
FieldSet.default_renderers[Geometry] = PyramidGeometryFieldRenderer


class DblPasswordField(Field):  # pragma: no cover
    def __init__(self, parent, original):
        self._original = original
        Field.__init__(self, name=original.name, value=original.value)
        self.parent = parent

        def passwords_match(value, field):
            value1 = field.renderer.params.getone(field.renderer.name)
            value2 = field.renderer.params.getone(field.renderer.name + "_confirm")
            if value1 != value2:
                raise ValidationError(_("Passwords do not match"))
        self.validators.append(passwords_match)

    def sync(self):
        value = self.renderer.params.getone(self.renderer.name)
        if len(value) > 0:
            setattr(self.model, self.name, value)

    def render(self):
        return (
            password_field(self.renderer.name, value="") +
            password_field(self.renderer.name + "_confirm", value=""))


class CheckBoxTreeSet(CheckBoxSet):  # pragma: no cover
    def __init__(self, attribute, dom_id, auto_check=True, auto_collapsed=True):
        super(CheckBoxTreeSet, self).__init__(attribute)
        self.dom_id = dom_id
        self.auto_check = auto_check
        self.auto_collapsed = auto_collapsed

    @staticmethod
    def render_tree():
        return ""

    def render(self, options, **kwargs):
        opt = u""
        if self.auto_collapsed:
            opt += u'"initializeUnchecked": "collapsed"'
        if self.auto_collapsed and not self.auto_check:
            opt += u","
        if not self.auto_check:
            opt += u"""'onCheck': {
                'others': false,
                'descendants': false,
                'ancestors': false },
            'onUncheck': {
                'others': false,
                'descendants': false,
                'ancestors': false }"""
        result = u"""<script lang="text/javascript" >
            $(document).ready(function(){{
                $("#{id!s}").checkboxTree({{{opt!s}}});
            }});
        </script>
        <ul id="{id!s}" class="checkboxtree">
        """.format(id=self.dom_id, opt=opt)
        result += self.render_tree()
        result += u"</ul>"
        return result


class SimpleLayerCheckBoxTreeSet(CheckBoxTreeSet):  # pragma: no cover

    def __init__(
            self, attribute, dom_id="layer_tree",
            auto_check=True, only_internal_wms=True):
        super(SimpleLayerCheckBoxTreeSet, self).__init__(attribute, dom_id, auto_check)
        self._rendered_id = []
        self.only_internal_wms = only_internal_wms

    def render_children(self, item, depth):
        # escape loop
        if (depth >= 5):
            return ""

        result = u""
        if isinstance(item, models.TreeGroup):
            result += u"<ul>"
            for child in item.children_relation:
                result += self.render_item(child, depth + 1)
            result += u"</ul>"
        return result

    def render_organisational_item(self, item, depth):
        if item in self.layer_group:
            self.layer_group.remove(item)

        result = u"<li>"
        if self.auto_check:
            result += u'<input type="checkbox"></input>'
        result += u"<label>{label!s}</label>".format(
            label=item.name,
        )
        result += self.render_children(item, depth)
        result += u"</li>"
        return result

    def is_checked(self, item, final_item):
        return final_item.id in self.values

    def build_values(self):
        self.values = [int(v) for v in self.value]

    def render_item(self, item, depth):
        final_item = item.treeitem if isinstance(item, models.LayergroupTreeitem) else item

        # no link to theme
        # if autocheck mean that we want select only layers.
        if isinstance(final_item, models.Theme) or \
                self.auto_check and not isinstance(final_item, models.Layer):
            return self.render_organisational_item(final_item, depth)

        # escape public layer if wanted
        if self.only_internal_wms and isinstance(final_item, models.LayerV1) \
                and final_item.layer_type != "internal WMS":
            return ""

        if final_item in self.layer_group:
            self.layer_group.remove(final_item)
        elif final_item in self.layer:
            self.layer.remove(final_item)

        prefixs = {
            "layerv1": "Layer V1: ",
            "l_wms": "WMS Layer: ",
            "l_wmts": "WMTS Layer: ",
        }

        result = u"""
        <li>
            <input type="checkbox" id="{id!s}" name="{name!s}" value="{value!s}"{add!s}></input>
            <label>{type!s}{label!s}</label>
            """.format(
            id="{}_{}".format(self.name, self.i),
            # adds -second to fields (layer) that appears two time to
            # don"t save them twice (=> integrity error).
            name=self.name + ("-second" if final_item.id in self._rendered_id else ""),
            value=final_item.id,
            add=' checked="checked"' if self.is_checked(item, final_item) else "",
            type=prefixs.get(final_item.item_type, ""),
            label=final_item.name,
        )
        self._rendered_id.append(final_item.id)
        self.i += 1
        result += self.render_children(final_item, depth)
        result += u"</li>"
        return result

    def render_tree(self):
        self.build_values()

        self.layer = models.DBSession.query(models.Layer).all()
        self.layer_group = models.DBSession.query(models.LayerGroup).all()
        themes = models.DBSession.query(models.Theme). \
            order_by(models.Theme.ordering).all()
        self.i = 0
        result = u""
        for item in themes:
            result += self.render_item(item, 1)

        # add unlinked layers
        if len(self.layer) >= 0 or len(self.layer_group) > 0:
            result += u"<li>"
            if self.auto_check:
                result += u'<input type="checkbox"></input>'
            result += u"<label>{name!s}</label>".format(name=_("Unlinked layers"))
            result += u"<ul>"

            while len(self.layer_group) > 0:
                result += self.render_item(self.layer_group.pop(0), 2)
            while len(self.layer) > 0:
                result += self.render_item(self.layer.pop(0), 2)

            result += u"</ul>"
            result += u"</li>"
        return result


class LayerCheckBoxTreeSet(SimpleLayerCheckBoxTreeSet):  # pragma: no cover
    def build_values(self):
        values = models.DBSession.query(models.LayergroupTreeitem) \
            .filter(models.LayergroupTreeitem.id.in_([int(v) for v in self.value])).all()
        self.values = [v.treeitem.id for v in values]


class TreeItemCheckBoxTreeSet(LayerCheckBoxTreeSet):  # pragma: no cover
    def __init__(self, attribute):
        super(TreeItemCheckBoxTreeSet, self).__init__(
            attribute,
            auto_check=False, only_internal_wms=False
        )


class FunctionalityCheckBoxTreeSet(CheckBoxTreeSet):  # pragma: no cover
    def __init__(self, attribute):
        super(FunctionalityCheckBoxTreeSet, self).__init__(
            attribute, dom_id="tree_func", auto_collapsed=False)

    def render_tree(self):
        query = models.DBSession.query(models.Functionality)
        query = query.order_by(models.Functionality.name)
        query = query.order_by(models.Functionality.value)
        functionalities = query.all()
        i = 0
        prev_name = u""
        result = u""
        for functionality in functionalities:
            if prev_name != functionality.name:
                if prev_name != u"":
                    result += u"</ul></li>\n"
                prev_name = functionality.name
                result += \
                    u'<li><input type="checkbox" style="display:none"></input>' \
                    '<label>%s</label><ul>\n' % (functionality.name)
            result += \
                u'<li><input type="checkbox" id="%s" name="%s" value="%i"%s>' \
                '</input><label>%s</label></li>\n' % (
                    "{0!s}_{1:d}".format(self.name, i),
                    self.name,
                    functionality.id,
                    u' checked="checked"' if self._is_checked(functionality.id) else "",
                    functionality.value)
            i += 1
        result += u"</ul></li>"
        return result


class RoListRenderer(FieldRenderer):  # pragma: no cover
    def render_readonly(self, **kwargs):
        return helpers.content_tag(u"span", ("," + helpers.tag("br")).join([
            helpers.literal(value) for value in self.raw_value
        ]), style=u"white-space: nowrap;")


##############################################################################
# FIELDS defs
#
# DefaultBasemap, Layer, LayerGroup, Mandant, Printtemplates, RestrictionArea,
# Role, Title, User
#
##############################################################################

image_type_options = [
    (_("image/jpeg"), "image/jpeg"),
    (_("image/png"), "image/png")
]
time_options = [
    (_("disabled"), "disabled"),
    (_("value"), "value"),
    (_("range"), "range"),
]
time_widget_options = [
    (_("slider"), "slider"),
    (_("datepicker"), "datepicker"),
]
ogcserver_type_options = [
    (_("MapServer"), models.OGCSERVER_TYPE_MAPSERVER),
    (_("QGISserver"), models.OGCSERVER_TYPE_QGISSERVER),
    (_("GeoServer"), models.OGCSERVER_TYPE_GEOSERVER),
    (_("Other"), models.OGCSERVER_TYPE_OTHER),
]
ogcserver_auth_options = [
    (_("No auth"), models.OGCSERVER_AUTH_NOAUTH),
    (_("Standard auth"), models.OGCSERVER_AUTH_STANDARD),
    (_("GeoServer auth"), models.OGCSERVER_AUTH_GEOSERVER),
]

# Layer V1
LayerV1 = FieldSet(models.LayerV1)
LayerV1.configure(exclude=[LayerV1.parents_relation])
LayerV1.layer_type.set(
    renderer=SelectFieldRenderer,
    options=[
        (_("internal WMS"), "internal WMS"),
        (_("external WMS"), "external WMS"),
        (_("WMTS"), "WMTS"),
        (_("no 2D"), "no 2D"),
    ])
LayerV1.image_type.set(
    renderer=SelectFieldRenderer,
    options=image_type_options
)
LayerV1.time_mode.set(
    renderer=SelectFieldRenderer,
    options=time_options,
)
LayerV1.time_widget.set(
    renderer=SelectFieldRenderer,
    options=time_widget_options,
)
LayerV1.interfaces.set(renderer=CheckBoxSet)
LayerV1.metadatas.set(renderer=RoListRenderer, readonly=True)
LayerV1.restrictionareas.set(renderer=CheckBoxSet)

# OGC server
OGCServer = FieldSet(models.OGCServer)
OGCServer.image_type.set(
    renderer=SelectFieldRenderer,
    options=image_type_options,
)
OGCServer.type.set(
    renderer=SelectFieldRenderer,
    options=ogcserver_type_options,
)
OGCServer.auth.set(
    renderer=SelectFieldRenderer,
    options=ogcserver_auth_options,
)

# LayerWMS
LayerWMS = FieldSet(models.LayerWMS)
LayerWMS.configure(exclude=[LayerWMS.parents_relation])
LayerWMS.time_mode.set(
    renderer=SelectFieldRenderer,
    options=time_options,
)
LayerWMS.time_widget.set(
    renderer=SelectFieldRenderer,
    options=time_widget_options,
)
LayerWMS.interfaces.set(renderer=CheckBoxSet)
LayerWMS.metadatas.set(renderer=RoListRenderer, readonly=True)
LayerWMS.dimensions.set(renderer=RoListRenderer, readonly=True)
LayerWMS.restrictionareas.set(renderer=CheckBoxSet)
LayerWMS.ogc_server.set(renderer=SelectFieldRenderer)


# LayerWMTS
LayerWMTS = FieldSet(models.LayerWMTS)
LayerWMTS.configure(exclude=[LayerWMTS.parents_relation])
LayerWMTS.image_type.set(
    renderer=SelectFieldRenderer,
    options=image_type_options
)
LayerWMTS.interfaces.set(renderer=CheckBoxSet)
LayerWMTS.metadatas.set(renderer=RoListRenderer, readonly=True)
LayerWMTS.dimensions.set(renderer=RoListRenderer, readonly=True)
LayerWMTS.restrictionareas.set(renderer=CheckBoxSet)


class ChildrenAttributeField(AttributeField):

    def __init__(self, *args, **kargs):
        AttributeField.__init__(self, *args, **kargs)

    def sync(self):  # pragma: no cover
        self.model.children = [
            self.parent.session.query(models.TreeItem).get(int(pk))
            for pk in self.renderer.deserialize()
        ]


# LayerGroup
LayerGroup = FieldSet(models.LayerGroup)
LayerGroup.configure(exclude=[LayerGroup.parents_relation, LayerGroup.children_relation])
LayerGroup.append(ChildrenAttributeField(
    manager_of_class(models.LayerGroup)["children_relation"], LayerGroup,
))
LayerGroup.children_relation.set(renderer=TreeItemCheckBoxTreeSet)
LayerGroup.metadatas.set(readonly=True)

# LayergroupTreeitem
LayergroupTreeitem = FieldSet(models.LayergroupTreeitem)
LayergroupTreeitem.ordering.set(metadata=dict(mandatory="")).required()

# Theme
Theme = FieldSet(models.Theme)
Theme.configure(exclude=[Theme.parents_relation, Theme.children_relation])
Theme.ordering.set(metadata=dict(mandatory="")).required()
Theme.append(ChildrenAttributeField(
    manager_of_class(models.Theme)["children_relation"], Theme
))
Theme.children_relation.set(renderer=TreeItemCheckBoxTreeSet)
Theme.functionalities.set(renderer=FunctionalityCheckBoxTreeSet)
Theme.interfaces.set(renderer=CheckBoxSet)
Theme.metadatas.set(readonly=True)
Theme.restricted_roles.set(renderer=CheckBoxSet)

# Functionality
Functionality = FieldSet(models.Functionality)
Functionality.name.set(
    renderer=SelectFieldRenderer,
    options=[(f, f) for f in formalchemy_available_functionalities])
Functionality.value.set(metadata=dict(mandatory="")).required()

# Interface
Interface = FieldSet(models.Interface)
Interface.configure(include=[Interface.name, Interface.description])

# Metadata
Metadata = FieldSet(models.Metadata)
Metadata.configure(include=[
    Metadata.item,
    Metadata.name,
    Metadata.value,
    Metadata.description
])
Metadata.name.set(
    renderer=SelectFieldRenderer,
    options=[(m, m) for m in formalchemy_available_metadata])
Metadata.value.set(metadata=dict(mandatory="")).required()

# Dimension
Dimension = FieldSet(models.Dimension)
Dimension.name.set(metadata=dict(mandatory="")).required()
Dimension.value.set(metadata=dict(mandatory="")).required()

# RestrictionArea
RestrictionArea = FieldSet(models.RestrictionArea)
RestrictionArea.name.set(metadata=dict(mandatory="")).required()
RestrictionArea.layers.set(renderer=SimpleLayerCheckBoxTreeSet)
RestrictionArea.roles.set(renderer=CheckBoxSet)
RestrictionArea.area.set(label=_(u"Restriction area"), options=[
    ("map_srid", 3857),
    ("base_layer", 'new OpenLayers.Layer.OSM("OSM")'),
    ("zoom", formalchemy_default_zoom),
    ("default_lon", formalchemy_default_x),
    ("default_lat", formalchemy_default_y)
])
field_order = [
    RestrictionArea.name,
    RestrictionArea.description,
    RestrictionArea.layers,
    RestrictionArea.roles,
    RestrictionArea.readwrite,
    RestrictionArea.area
]
RestrictionArea.configure(include=field_order)

# Role
Role = FieldSet(models.Role)
Role.name.set(metadata=dict(mandatory="")).required()
Role.functionalities.set(renderer=FunctionalityCheckBoxTreeSet)
Role.restrictionareas.set(renderer=CheckBoxSet)
Role.extent.set(label=_(u"Extent"), options=[
    ("map_srid", 3857),
    ("base_layer", 'new OpenLayers.Layer.OSM("OSM")'),
    ("zoom", formalchemy_default_zoom),
    ("default_lon", formalchemy_default_x),
    ("default_lat", formalchemy_default_y)
])
field_order = [
    Role.name,
    Role.description,
    Role.functionalities,
    Role.restrictionareas,
    Role.extent
]
Role.configure(include=field_order)

# User
User = FieldSet(models.User)


def _get_roles(parent):  # pragma: no cover
    return [
        (role.name, role.name)
        for role in parent.session.query(models.Role).all()
    ]


User.role_name.set(
    renderer=SelectFieldRenderer,
    options=_get_roles,
)
password = DblPasswordField(User, User._password)
User.append(password)
field_order = [
    User.username.validate(unique_validator).with_metadata(mandatory=""),
    password,
    User.role_name
]
if hasattr(User, "parent_role_name"):  # pragma: no cover
    field_order.append(User.parent_role_name)
field_order.extend([
    User.email.with_metadata(mandatory="")
])
User.configure(include=field_order)

#############################################################################
# GRID defs
#
# DefaultBasemapGrid, LayerGrid, LayerGroupGrid, MandantGrid,
# PrinttemplatesGrid, RestrictionAreaGrid, RoleGrid, TitleGrid, UserGrid
#
#############################################################################

# LayerV1Grid
LayerV1Grid = Grid(models.LayerV1)
field_order = [
    LayerV1.name,
    LayerV1.public,
    LayerV1.is_checked,
    LayerV1.icon,
    LayerV1.legend,
    LayerV1.identifier_attribute_field
]
LayerV1Grid.configure(include=field_order)

# LayerWMTSGrid
LayerWMTSGrid = Grid(models.LayerWMTS)
field_order = [
    LayerWMTS.name,
    LayerWMTS.public,
    LayerWMTS.layer
]
LayerWMTSGrid.configure(include=field_order)

# LayerGroupGrid
LayerGroupGrid = Grid(models.LayerGroup)
LayerGroupGrid.configure(exclude=[LayerGroupGrid.children_relation])

# LayergroupTreeitemGrid
LayergroupTreeitemGrid = Grid(models.LayergroupTreeitem)

# ThemeGrid
ThemeGrid = Grid(models.Theme)
ThemeGrid.configure(exclude=[ThemeGrid.parents_relation, ThemeGrid.children_relation])

# FunctionalityGrid
FunctionalityGrid = Grid(models.Functionality)

# InterfaceGrid
InterfaceGrid = Grid(models.Interface)

# MetadataGrid
MetadataGrid = Grid(models.Metadata)

# DimensionGrid
DimensionGrid = Grid(models.Dimension)

# RestrictionAreaGrid
RestrictionAreaGrid = Grid(models.RestrictionArea)
field_order = [
    RestrictionArea.name,
    RestrictionArea.description,
    RestrictionAreaGrid.roles
]
RestrictionAreaGrid.configure(include=field_order)

# RoleGrid
RoleGrid = Grid(models.Role)
field_order = [
    Role.name,
    Role.description,
    RoleGrid.functionalities,
    RoleGrid.restrictionareas,
]
RoleGrid.configure(include=field_order)

# UserGrid
UserGrid = Grid(models.User)
field_order = [User.username, User.role_name]
if hasattr(UserGrid, "parent_role"):  # pragma: no cover
    field_order.append(User.parent_role_name)
UserGrid.configure(include=field_order)
