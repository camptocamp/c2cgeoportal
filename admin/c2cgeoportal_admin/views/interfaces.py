import colander
from c2cgeoform.ext.deform_ext import RelationCheckBoxListWidget
from c2cgeoform.schema import (
    GeoFormManyToManySchemaNode,
    manytomany_validator,
)
from c2cgeoportal_commons.models.main import Interface
from functools import partial
from pyramid.view import view_defaults
from pyramid.view import view_config

from c2cgeoform.schema import GeoFormSchemaNode

from c2cgeoform.views.abstract_views import AbstractViews
from c2cgeoform.views.abstract_views import ListField

interfaces_schema_node = colander.SequenceSchema(
    GeoFormManyToManySchemaNode(Interface),
    name='interfaces',
    widget=RelationCheckBoxListWidget(
        Interface,
        'id',
        'name',
        order_by='name',
        edit_url=lambda request, value: request.route_url(
            'c2cgeoform_item',
            table='interfaces',
            id=value
        )
    ),
    validator=manytomany_validator
)

_list_field = partial(ListField, Interface)

base_schema = GeoFormSchemaNode(Interface)


@view_defaults(match_param='table=interfaces')
class InterfacesViews(AbstractViews):
    _list_fields = [
        _list_field('name'),
        _list_field('description'),
        _list_field(
            'layers',
            renderer=lambda interface: ', '.join([l.name or ''
                                                 for l in interface.layers])),
        _list_field(
            'theme',
            renderer=lambda interface: ', '.join(['{}-{}'.format(t.name, t.name) or ''
                                                  for t in interface.theme]))
    ]
    _id_field = 'id'
    _model = Interface
    _base_schema = base_schema

    @view_config(route_name='c2cgeoform_index',
                 renderer='../templates/index.jinja2')
    def index(self):
        return super().index()

    @view_config(route_name='c2cgeoform_grid',
                 renderer='json')
    def grid(self):
        return super().grid()

    @view_config(route_name='c2cgeoform_item',
                 request_method='GET',
                 renderer='../templates/edit.jinja2')
    def view(self):
        return super().edit()

    @view_config(route_name='c2cgeoform_item',
                 request_method='POST',
                 renderer='../templates/edit.jinja2')
    def save(self):
        return super().save()

    @view_config(route_name='c2cgeoform_item',
                 request_method='DELETE')
    def delete(self):
        return super().delete()

    @view_config(route_name='c2cgeoform_item_action',
                 request_method='GET',
                 renderer='../templates/edit.jinja2')
    def duplicate(self):
        return super().duplicate()
