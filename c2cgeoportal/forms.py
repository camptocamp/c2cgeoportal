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


import logging
import os

from fanstatic import Library, Group, Resource
from fanstatic.core import set_resource_file_existence_checking
from pyramid_formalchemy.utils import TemplateEngine
from formalchemy import config as fa_config
from formalchemy import fields
from formalchemy import FieldSet, Grid
from formalchemy.fields import Field, CheckBoxSet
from formalchemy.validators import ValidationError
from formalchemy.helpers import password_field
from mako.lookup import TemplateLookup
from fa.jquery import renderers as fa_renderers
from fa.jquery import fanstatic_resources
from pyramid_formalchemy import events as fa_events
from geoformalchemy.base import GeometryFieldRenderer
from geoalchemy import geometry
from pyramid.i18n import TranslationStringFactory

from c2cgeoportal import models
from c2cgeoportal import (
    formalchemy_default_zoom,
    formalchemy_default_x, formalchemy_default_y,
    formalchemy_available_functionalities)

__all__ = [
    'Functionality', 'User', 'Role', 'LayerGroup', 'Theme', 'Layer',
    'RestrictionArea', 'LayerGrid', 'LayerGroupGrid', 'ThemeGrid',
    'FunctionalityGrid', 'RestrictionAreaGrid', 'RoleGrid', 'UserGrid']


log = logging.getLogger(__name__)
_ = TranslationStringFactory('c2cgeoportal')

fa_config.encoding = 'utf-8'
fa_config.engine = TemplateEngine()

fanstatic_lib = Library('admin', 'static')
admin_js = Resource(
    fanstatic_lib,
    'build/admin/admin.js',
    depends=[fanstatic_resources.jqueryui])
admin_css = Resource(
    fanstatic_lib,
    'build/admin/admin.css',
    depends=[fanstatic_resources.fa_uiadmin_css])

# HACK to invoke fanstatic to inject a script which content is dynamic:
# the content of the script sets OpenLayers.ImgPath to an url that is
# dynamically generated using request.static_url
olimgpath_js = None
# deactive resource checking in fanstatic
set_resource_file_existence_checking(False)


def get_fanstatic_resources(request):  # pragma: no cover
    global olimgpath_js
    olimgpath = request.static_url('c2cgeoportal:static/lib/openlayers/img/')

    def olimgpath_renderer(url):
        return '<script>OpenLayers.ImgPath="%s";</script>' % olimgpath
    if olimgpath_js is None:
        olimgpath_js = Resource(
            fanstatic_lib,
            'whatever.js',
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
        raise ValidationError(_(u'Duplicate record'))


class PyramidGeometryFieldRenderer(GeometryFieldRenderer):  # pragma: no cover
    def __init__(self, field):
        self.__templates = None
        GeometryFieldRenderer.__init__(self, field)

    def get_templates(self):
        if self.__templates is None:
            self.__templates = TemplateLookup(
                [os.path.join(os.path.dirname(__file__), 'templates', 'admin')],
                input_encoding='utf-8', output_encoding='utf-8')
        return self.__templates


FieldSet.default_renderers.update(fa_renderers.default_renderers)
FieldSet.default_renderers[geometry.Geometry] = PyramidGeometryFieldRenderer
FieldSet.default_renderers[geometry.Polygon] = PyramidGeometryFieldRenderer


class DblPasswordField(Field):  # pragma: no cover
    def __init__(self, parent, original):
        self._original = original
        Field.__init__(self, name=original.name, value=original.value)
        self.parent = parent

        def passwords_match(value, field):
            value1 = field.renderer.params.getone(field.renderer.name)
            value2 = field.renderer.params.getone(field.renderer.name + '_confirm')
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
            password_field(self.renderer.name + '_confirm', value=""))


class CheckBoxTreeSet(CheckBoxSet):  # pragma: no cover
    def __init__(self, attribute, dom_id, auto_check=True, auto_collapsed=True):
        super(CheckBoxTreeSet, self).__init__(attribute)
        self.dom_id = dom_id
        self.auto_check = auto_check
        self.auto_collapsed = auto_collapsed

    def render_tree(self):
        return ""

    def render(self, options, **kwargs):
        opt = ""
        if self.auto_collapsed:
            opt += '"initializeUnchecked": "collapsed"'
        if self.auto_collapsed and not self.auto_check:
            opt += ","
        if not self.auto_check:
            opt += """'onCheck': {
                'others': false,
                'descendants': false,
                'ancestors': false },
            'onUncheck': {
                'others': false,
                'descendants': false,
                'ancestors': false }"""
        result = """<script lang="text/javascript" >
            $(document).ready(function(){
                $("#%(id)s").checkboxTree({%(opt)s});
            });
        </script>
        <ul id="%(id)s" class="checkboxtree">
        """ % {'id': self.dom_id, 'opt': opt}
        result += self.render_tree()
        result += '</ul>'
        return result


class LayerCheckBoxTreeSet(CheckBoxTreeSet):  # pragma: no cover

    def __init__(
            self, attribute, dom_id='layer_tree',
            auto_check=True, only_internal_wms=True):
        super(LayerCheckBoxTreeSet, self).__init__(attribute, dom_id, auto_check)
        self._rendered_id = []
        self.only_internal_wms = only_internal_wms

    def render_children(self, item, depth):
        # escape loop
        if (depth >= 5):
            return ""

        result = ""
        if isinstance(item, models.TreeGroup):
            result += "<ul>"
            for child in item.children:
                result += self.render_item(child, depth + 1)
            result += "</ul>"
        return result

    def render_organisational_item(self, item, depth):
        if item in self.layer_group:
            self.layer_group.remove(item)

        result = "<li>"
        if self.auto_check:
            result += '<input type="checkbox"></input>'
        result += "<label>%(label)s</label>" % {'label': item.name}
        result += self.render_children(item, depth)
        result += '</li>'
        return result

    def render_item(self, item, depth):
        # no link to theme
        # if autocheck mean that we want select only layers.
        if isinstance(item, models.Theme) or \
                self.auto_check and not isinstance(item, models.Layer):
            return self.render_organisational_item(item, depth)

        # escape public layer if wanted
        if self.only_internal_wms and isinstance(item, models.Layer) \
                and item.layerType != "internal WMS":
            return ""

        if item in self.layer_group:
            self.layer_group.remove(item)
        elif item in self.layer:
            self.layer.remove(item)

        result = """
        <li>
            <input type="checkbox" id="%(id)s" name="%(name)s" value="%(value)s"%(add)s></input>
            <label>%(label)s</label>
            """ % {
            'id': '%s_%i' % (self.name, self.i),
            # adds -second to fields (layer) that appears two time to
            # don't save them twice (=> integrity error).
            'name': self.name + ("-second" if item.id in self._rendered_id else ""),
            'value': item.id,
            'add': ' checked="checked"' if self._is_checked(item.id) else "",
            'label': item.name
        }
        self._rendered_id.append(item.id)
        self.i += 1
        result += self.render_children(item, depth)
        result += '</li>'
        return result

    def render_tree(self):
        self.layer = models.DBSession.query(models.Layer). \
            order_by(models.Layer.order).all()
        self.layer_group = models.DBSession.query(models.LayerGroup). \
            order_by(models.LayerGroup.order).all()
        themes = models.DBSession.query(models.Theme). \
            order_by(models.Theme.order).all()
        self.i = 0
        result = ""
        for item in themes:
            result += self.render_item(item, 1)

        # add unlinked layers
        if len(self.layer) >= 0 or len(self.layer_group) > 0:
            result += "<li>"
            if self.auto_check:
                result += '<input type="checkbox"></input>'
            result += "<label>%(name)s</label>" % {'name': _('Unlinked layers')}
            result += "<ul>"

            while len(self.layer_group) > 0:
                result += self.render_item(self.layer_group.pop(0), 2)
            while len(self.layer) > 0:
                result += self.render_item(self.layer.pop(0), 2)

            result += "</ul>"
            result += '</li>'
        return result


class TreeItemCheckBoxTreeSet(LayerCheckBoxTreeSet):  # pragma: no cover
    def __init__(self, attribute):
        super(TreeItemCheckBoxTreeSet, self).__init__(
            attribute,
            auto_check=False, only_internal_wms=False)


class FunctionalityCheckBoxTreeSet(CheckBoxTreeSet):  # pragma: no cover
    def __init__(self, attribute):
        super(FunctionalityCheckBoxTreeSet, self).__init__(
            attribute, dom_id='tree_func', auto_collapsed=False)

    def render_tree(self):
        query = models.DBSession.query(models.Functionality)
        query = query.order_by(models.Functionality.name)
        query = query.order_by(models.Functionality.value)
        functionalities = query.all()
        i = 0
        prev_name = u''
        result = u""
        for functionality in functionalities:
            if prev_name != functionality.name:
                if prev_name != u'':
                    result += '</ul></li>\n'
                prev_name = functionality.name
                result += \
                    '<li><input type="checkbox" style="display:none"></input>' \
                    '<label>%s</label><ul>\n' % (functionality.name)
            result += \
                '<li><input type="checkbox" id="%s" name="%s" value="%i"%s>' \
                '</input><label>%s</label></li>\n' % (
                    '%s_%i' % (self.name, i),
                    self.name,
                    functionality.id,
                    ' checked="checked"' if self._is_checked(functionality.id) else "",
                    functionality.value)
            i += 1
        result += '</ul></li>'
        return result

##############################################################################
# FIELDS defs
#
# DefaultBasemap, Layer, LayerGroup, Mandant, Printtemplates, RestrictionArea,
# Role, Title, User
#
##############################################################################

# Layer
Layer = FieldSet(models.Layer)
Layer.order.set(metadata=dict(mandatory='')).required()
Layer.layerType.set(
    renderer=fields.SelectFieldRenderer,
    options=["internal WMS", "external WMS", "WMTS", "no 2D"])
Layer.imageType.set(
    renderer=fields.SelectFieldRenderer,
    options=["image/jpeg", "image/png"])
Layer.restrictionareas.set(renderer=fields.CheckBoxSet)
Layer.parents.set(readonly=True)

# LayerGroup
LayerGroup = FieldSet(models.LayerGroup)
LayerGroup.order.set(metadata=dict(mandatory='')).required()
LayerGroup.children.set(renderer=TreeItemCheckBoxTreeSet)
LayerGroup.parents.set(readonly=True)

# Theme
Theme = FieldSet(models.Theme)
Theme.order.set(metadata=dict(mandatory='')).required()
Theme.children.set(renderer=TreeItemCheckBoxTreeSet)
Theme.configure(exclude=[Theme.parents])

# Functionality
Functionality = FieldSet(models.Functionality)
Functionality.name.set(
    renderer=fields.SelectFieldRenderer,
    options=formalchemy_available_functionalities)
Functionality.value.set(metadata=dict(mandatory='')).required()

# RestrictionArea
RestrictionArea = FieldSet(models.RestrictionArea)
RestrictionArea.name.set(metadata=dict(mandatory='')).required()
RestrictionArea.layers.set(renderer=LayerCheckBoxTreeSet)
RestrictionArea.roles.set(renderer=fields.CheckBoxSet)
RestrictionArea.area.set(label=_(u'Restriction area'), options=[
    ('map_srid', 3857),
    ('base_layer', 'new OpenLayers.Layer.OSM("OSM")'),
    ('zoom', formalchemy_default_zoom),
    ('default_lon', formalchemy_default_x),
    ('default_lat', formalchemy_default_y),
    # if we specify None or '' GeoFolmAlchemy will add a script from openlayers.org
    # and we want to use our own build script.
    ('openlayers_lib', 'none')
])
fieldOrder = [RestrictionArea.name,
              RestrictionArea.description,
              RestrictionArea.layers,
              RestrictionArea.roles,
              RestrictionArea.readwrite,
              RestrictionArea.area]
RestrictionArea.configure(include=fieldOrder)

# Role
Role = FieldSet(models.Role)
Role.name.set(metadata=dict(mandatory='')).required()
Role.functionalities.set(renderer=FunctionalityCheckBoxTreeSet)
Role.restrictionareas.set(renderer=fields.CheckBoxSet)
Role.users.set(readonly=True)
Role.extent.set(label=_(u'Extent'), options=[
    ('map_srid', 3857),
    ('base_layer', 'new OpenLayers.Layer.OSM("OSM")'),
    ('zoom', formalchemy_default_zoom),
    ('default_lon', formalchemy_default_x),
    ('default_lat', formalchemy_default_y),
    # if we specify None or '' GeoFolmAlchemy will add a script from openlayers.org
    # and we want to use our own build script.
    ('openlayers_lib', 'none')
])
fieldOrder = [Role.name,
              Role.description,
              Role.functionalities,
              Role.restrictionareas,
              Role.users,
              Role.extent]
Role.configure(include=fieldOrder)

# User
User = FieldSet(models.User)
password = DblPasswordField(User, User._password)
User.append(password)
fieldOrder = [
    User.username.validate(unique_validator).with_metadata(mandatory=''),
    password,
    User.role
]
if hasattr(User, 'parent_role'):  # pragma: no cover
    fieldOrder.append(User.parent_role)
fieldOrder.extend([
    User.functionalities.set(renderer=FunctionalityCheckBoxTreeSet),
    User.email.with_metadata(mandatory='')
])
User.configure(include=fieldOrder)

#############################################################################
# GRID defs
#
# DefaultBasemapGrid, LayerGrid, LayerGroupGrid, MandantGrid,
# PrinttemplatesGrid, RestrictionAreaGrid, RoleGrid, TitleGrid, UserGrid
#
#############################################################################

# LayerGrid
LayerGrid = Grid(models.Layer)
fieldOrder = [Layer.name,
              Layer.public,
              Layer.inDesktopViewer,
              Layer.inMobileViewer,
              Layer.isChecked,
              Layer.icon,
              Layer.legend,
              Layer.identifierAttributeField]
LayerGrid.configure(include=fieldOrder)

# LayerGroupGrid
LayerGroupGrid = Grid(models.LayerGroup)

# ThemeGrid
ThemeGrid = Grid(models.Theme)
ThemeGrid.configure(exclude=[ThemeGrid.parents])

# FunctionalityGrid
FunctionalityGrid = Grid(models.Functionality)

# RestrictionAreaGrid
RestrictionAreaGrid = Grid(models.RestrictionArea)
fieldOrder = [RestrictionArea.name,
              RestrictionArea.description,
              RestrictionAreaGrid.roles]
RestrictionAreaGrid.configure(include=fieldOrder)

# RoleGrid
RoleGrid = Grid(models.Role)
fieldOrder = [Role.name,
              Role.description,
              RoleGrid.functionalities,
              RoleGrid.restrictionareas,
              RoleGrid.users]
RoleGrid.configure(include=fieldOrder)

# UserGrid
UserGrid = Grid(models.User)
fieldOrder = [User.username, User.functionalities, User.role]
if hasattr(UserGrid, 'parent_role'):  # pragma: no cover
    fieldOrder.append(User.parent_role)
UserGrid.configure(include=fieldOrder)
