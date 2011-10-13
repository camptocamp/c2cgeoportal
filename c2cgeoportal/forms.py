# -*- coding: utf-8 -*-
import logging
import os

from fanstatic import Library, Group, Resource
from fanstatic.core import set_resource_file_existence_checking
from pyramid.i18n import Localizer
from pyramid_formalchemy.utils import TemplateEngine
from sqlalchemy import UniqueConstraint
from formalchemy import config as fa_config
from formalchemy import templates
from formalchemy import fields
from formalchemy import forms
from formalchemy import tables
from formalchemy import FieldSet, Grid
from formalchemy.fields import Field, CheckBoxSet
from formalchemy.validators import ValidationError
from formalchemy.helpers import password_field
from formalchemy.ext.fsblob import FileFieldRenderer
from formalchemy.ext.fsblob import ImageFieldRenderer
from mako.lookup import TemplateLookup
from fa.jquery import renderers as fa_renderers
from fa.jquery import fanstatic_resources
from pyramid_formalchemy import events as fa_events
from geoformalchemy.base import GeometryFieldRenderer
from geoalchemy import geometry
from pyramid.i18n import TranslationStringFactory

from c2cgeoportal import models
from c2cgeoportal import (formalchemy_language, formalchemy_default_zoom,
                           formalchemy_default_lon, formalchemy_default_lat,
                           formalchemy_available_functionalities)

__all__ = ['Functionality', 'User', 'Role', 'LayerGroup', 'Theme', 'Layer',
'RestrictionArea', 'LayerGrid', 'LayerGroupGrid', 'ThemeGrid',
'FunctionalityGrid', 'RestrictionAreaGrid', 'RoleGrid', 'UserGrid']


log = logging.getLogger(__name__)
_ = TranslationStringFactory('c2cgeoportal')

fa_config.encoding = 'utf-8'
fa_config.engine = TemplateEngine()

fanstatic_lib = Library('admin', 'static/build')
admin_js = Resource(
        fanstatic_lib,
        'admin/admin.js',
        depends=[fanstatic_resources.jqueryui])
admin_css = Resource(
        fanstatic_lib,
        'admin/admin.css',
        depends=[fanstatic_resources.fa_uiadmin_css])

# HACK to invoke fanstatic to inject a script which content is dynamic:
# the content of the script sets OpenLayers.ImgPath to an url that is
# dynamically generated using request.static_url
olimgpath_js = None
# deactive resource checking in fanstatic
set_resource_file_existence_checking(False)
def get_fanstatic_resources(request):
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
def before_render_functionnality(context, event):
    get_fanstatic_resources(event.request).need()

@fa_events.subscriber([models.Theme, fa_events.IBeforeRenderEvent])
def before_render_theme(context, event):
    get_fanstatic_resources(event.request).need()

@fa_events.subscriber([models.Layer, fa_events.IBeforeRenderEvent])
def before_render_layer(context, event):
    get_fanstatic_resources(event.request).need()

@fa_events.subscriber([models.LayerGroup, fa_events.IBeforeRenderEvent])
def before_render_layergroup(context, event):
    get_fanstatic_resources(event.request).need()

@fa_events.subscriber([models.RestrictionArea, fa_events.IBeforeRenderEvent])
def before_render_restrictionarea(context, event):
    get_fanstatic_resources(event.request).need()

@fa_events.subscriber([models.Role, fa_events.IBeforeRenderEvent])
def before_render_role(context, event):
    get_fanstatic_resources(event.request).need()

@fa_events.subscriber([models.User, fa_events.IBeforeRenderEvent])
def before_render_user(context, event):
    get_fanstatic_resources(event.request).need()

# validator to check uniqueness of unique key in db (prevent duplicate key error)
def unique_validator(value,f):
    if f.parent._bound_pk is None and f.query(f.model.__class__).filter_by(
                                                     **{f.name:f.value} ).first():
        raise ValidationError(_(u'Duplicate record'))

class PyramidGeometryFieldRenderer(GeometryFieldRenderer):
    def __init__(self, field):
        self.__templates = None
        GeometryFieldRenderer.__init__(self, field)

    def get_templates (self):
        if self.__templates == None:
            self.__templates = TemplateLookup(
                [os.path.join(os.path.dirname(__file__), 'templates', 'admin')], 
                input_encoding='utf-8', output_encoding='utf-8')
        return self.__templates


FieldSet.default_renderers.update(fa_renderers.default_renderers)
FieldSet.default_renderers[geometry.Geometry] = PyramidGeometryFieldRenderer
FieldSet.default_renderers[geometry.Polygon] = PyramidGeometryFieldRenderer

class DblPasswordField(Field):
    def __init__(self, parent, original):
        self._original = original
        Field.__init__(self, name = original.name, value = original.value)
        self.parent = parent
        clsname = self.parent.model.__class__.__name__
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
        return (password_field(self.renderer.name, value="")
            + password_field(self.renderer.name + '_confirm', value=""))

####################################################################################
# FIELDS defs
#
# DefaultBasemap, Layer, LayerGroup, Mandant, Printtemplates, RestrictionArea,
# Role, Title, User
#
####################################################################################

# Layer
Layer = FieldSet(models.Layer)
Layer.order.set(metadata=dict(mandatory='')).required()
Layer.layerType.set(renderer=fields.SelectFieldRenderer, \
        options=["internal WMS", "external WMS", "internal WMTS",
                 "external WMTS", "empty"])
Layer.imageType.set(renderer=fields.SelectFieldRenderer, \
        options=["image/jpeg", "image/png"])
Layer.restrictionareas.set(renderer=fields.CheckBoxSet)
Layer.parents.set(readonly=True)

# LayerGroup
LayerGroup = FieldSet(models.LayerGroup)
LayerGroup.order.set(metadata=dict(mandatory='')).required()
LayerGroup.children.set(size=20)
LayerGroup.parents.set(readonly=True)

# Theme
Theme = FieldSet(models.Theme)
Theme.order.set(metadata=dict(mandatory='')).required()
Theme.children.set(size=20)
Theme.configure(exclude=[Theme.parents])

# Functionality
Functionality = FieldSet(models.Functionality)
Functionality.name.set(renderer=fields.SelectFieldRenderer,  \
        options=formalchemy_available_functionalities.split())
Functionality.value.set(metadata=dict(mandatory='')).required()

# RestrictionArea
RestrictionArea = FieldSet(models.RestrictionArea)
RestrictionArea.name.set(metadata=dict(mandatory='')).required()
class CheckBoxTreeSet(CheckBoxSet):
    def render(self, options, **kwargs):
        layer_groups = models.DBSession.query(models.LayerGroup).order_by(models.LayerGroup.name).all()
        result = '<script lang="text/javascript" >\n'
        result += '$(document).ready(function(){\n'
        result += '$("#tree_layer").checkboxTree({"initializeUnchecked": "collapsed"});\n'
        result += '});\n'
        result += '</script>\n'
        result += '<ul id="tree_layer">\n'
        i = 0
        for group in layer_groups:
            result += '<li><input type="checkbox"></input><label>%s</label><ul>\n' % \
                    (group.name)
            for layer in group.children:
                if type(layer) == models.Layer and layer.public == False:
                    result += '<li><input type="checkbox" id="%s" name="%s" value="%i"%s></input><label>%s</label></li>\n' % \
                            ('%s_%i' % (self.name, i),
                            self.name,
                            layer.id,
                            ' checked="checked"' if self._is_checked(layer.id) else "",
                            layer.name)
                    i += 1
            result += '</ul></li>\n'
        result += '</ul>'
        return result
RestrictionArea.layers.set(renderer=CheckBoxTreeSet)
RestrictionArea.roles.set(renderer=fields.CheckBoxSet)
RestrictionArea.area.set(label=_(u'Restriction area'), options=[
    ('map_srid', 900913),
    ('base_layer', 'new OpenLayers.Layer.OSM("OSM")'),
    ('zoom', formalchemy_default_zoom),
    ('default_lon', formalchemy_default_lon),
    ('default_lat', formalchemy_default_lat),
    # if we specify None or '' GeoFolmAlchemy will add a script from openlayers.org
    # and we want to use our own build script.
    ('openlayers_lib', 'none')
    ])
fieldOrder = [RestrictionArea.name,
              RestrictionArea.description,
              RestrictionArea.layers,
              RestrictionArea.roles,
              RestrictionArea.area]
RestrictionArea.configure(include=fieldOrder)

class FunctionalityCheckBoxTreeSet(CheckBoxSet):
    def render(self, options, **kwargs):
        functionalities = models.DBSession.query(models.Functionality). \
                          order_by(models.Functionality.name). \
                          order_by(models.Functionality.value).all()
        result = '<script lang="text/javascript" >\n'
        result += '$(document).ready(function(){\n'
        result += '$("#tree_layer").checkboxTree({"initializeUnchecked": "collapsed"});\n'
        result += '});\n'
        result += '</script>\n'
        result += '<ul id="tree_layer">\n'
        i = 0
        prev_name = u''
        for functionality in functionalities:
            if prev_name != functionality.name:
                if prev_name != u'':
                    result += '</ul></li>\n'
                prev_name = functionality.name
                result += '<li><input type="checkbox" style="display:none"></input><label>%s</label><ul>\n' \
                          % (functionality.name)
            result += '<li><input type="checkbox" id="%s" name="%s" value="%i"%s></input><label>%s</label></li>\n' % \
                ('%s_%i' % (self.name, i),
                self.name,
                functionality.id,
                ' checked="checked"' if self._is_checked(functionality.id) else "",
                functionality.value)
            i += 1
        result += '</ul></li></ul>\n'
        return result 

# Role
Role = FieldSet(models.Role)
Role.name.set(metadata=dict(mandatory='')).required()
Role.functionalities.set(renderer=FunctionalityCheckBoxTreeSet)
Role.restrictionareas.set(renderer=fields.CheckBoxSet)
Role.users.set(readonly=True)
Role.extent.set(label=_(u'Extent'), options=[
    ('map_srid', 900913),
    ('base_layer', 'new OpenLayers.Layer.OSM("OSM")'),
    ('zoom', formalchemy_default_zoom),
    ('default_lon', formalchemy_default_lon),
    ('default_lat', formalchemy_default_lat),
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
fieldOrder = [User.username.validate(unique_validator)
                               .with_metadata(mandatory=''),
              password,
              User.role]
if hasattr(User, 'parent_role'):
    fieldOrder.append(User.parent_role)
fieldOrder.extend([User.functionalities.set(renderer=FunctionalityCheckBoxTreeSet),
              User.email.with_metadata(mandatory='')])
User.configure(include=fieldOrder)

####################################################################################
# GRID defs
#
# DefaultBasemapGrid, LayerGrid, LayerGroupGrid, MandantGrid, PrinttemplatesGrid,
# RestrictionAreaGrid, RoleGrid, TitleGrid, UserGrid
#
####################################################################################

# LayerGrid
LayerGrid = Grid(models.Layer)

# LayerGroupGrid
LayerGroupGrid = Grid(models.LayerGroup)

# ThemeGrid
ThemeGrid = Grid(models.Theme)

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
if hasattr(UserGrid, 'parent_role'):
    fieldOrder.append(User.parent_role)
UserGrid.configure(include=fieldOrder)
