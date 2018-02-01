from functools import partial
from pyramid.view import view_defaults
from pyramid.view import view_config

import colander
from c2cgeoform.ext.deform_ext import RelationCheckBoxListWidget
from c2cgeoform.schema import (
    GeoFormSchemaNode,
    GeoFormManyToManySchemaNode,
    manytomany_validator,
)
from c2cgeoform.views.abstract_views import AbstractViews, ListField
from sqlalchemy import select
from sqlalchemy.orm import subqueryload
from sqlalchemy.sql.functions import concat

from c2cgeoportal_commons.models.main import Role, Functionality, RestrictionArea
from c2cgeoportal_admin.schemas.map import map_widget

_list_field = partial(ListField, Role)


base_schema = GeoFormSchemaNode(Role)
base_schema['extent'].widget = map_widget
base_schema.add_before(
    'extent',
    colander.SequenceSchema(
        GeoFormManyToManySchemaNode(Functionality),
        name='functionalities',
        widget=RelationCheckBoxListWidget(
            select([
                Functionality.id,
                concat(Functionality.name, '=', Functionality.value).label('label')
            ]).alias('functionnality_labels'),
            'id',
            'label',
            order_by='label',
            edit_url=lambda request, value: request.route_url(
                'c2cgeoform_item',
                table='functionalities', id=value
            )
        ),
        validator=manytomany_validator
    )
)
base_schema.add_before(
    'extent',
    colander.SequenceSchema(
        GeoFormManyToManySchemaNode(RestrictionArea),
        name='restrictionareas',
        widget=RelationCheckBoxListWidget(
            RestrictionArea,
            'id',
            'name',
            order_by='name',
            edit_url=lambda request, value: request.route_url(
                'c2cgeoform_item',
                table='restrictionareas',
                id=value
            )
        ),
        validator=manytomany_validator
    )
)


@view_defaults(match_param='table=roles')
class RoleViews(AbstractViews):
    _list_fields = [
        _list_field('name'),
        _list_field('description'),
        _list_field(
            'functionalities',
            renderer=lambda role: ', '.join(['{}={}'.format(f.name, f.value) for f in role.functionalities])
        ),
        _list_field(
            'restrictionareas',
            renderer=lambda role: ', '.join([r.name or '' for r in role.restrictionareas])
        ),
    ]
    _id_field = 'id'
    _model = Role
    _base_schema = base_schema

    def _base_query(self):
        return self._request.dbsession.query(Role). \
            options(subqueryload('functionalities')). \
            options(subqueryload('restrictionareas'))

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
