from functools import partial
from pyramid.view import view_defaults
from pyramid.view import view_config

import colander
from sqlalchemy import select
from sqlalchemy.orm import subqueryload
from sqlalchemy.sql.functions import concat
from c2cgeoform.ext.deform_ext import RelationCheckBoxListWidget
from c2cgeoform.schema import (
    GeoFormSchemaNode,
    GeoFormManyToManySchemaNode,
    manytomany_validator,
)
from c2cgeoform.views.abstract_views import ListField

from c2cgeoportal_commons.models.main import Theme, Interface, Role, Functionality
from c2cgeoportal_admin.views.treeitems import TreeItemViews

_list_field = partial(ListField, Theme)

base_schema = GeoFormSchemaNode(Theme)

base_schema.add(
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
            order_by='label'
        ),
        validator=manytomany_validator
    )
)

base_schema.add(
    colander.SequenceSchema(
        GeoFormManyToManySchemaNode(Role),
        name='restricted_roles',
        widget=RelationCheckBoxListWidget(
            Role,
            'id',
            'name',
            order_by='name'
        ),
        validator=manytomany_validator
    )
)

base_schema.add(
    colander.SequenceSchema(
        GeoFormManyToManySchemaNode(Interface),
        name='interfaces',
        widget=RelationCheckBoxListWidget(
            Interface,
            'id',
            'name',
            order_by='name'
        ),
        validator=manytomany_validator
    )
)


@view_defaults(match_param='table=themes')
class ThemeViews(TreeItemViews):

    _list_fields = TreeItemViews._list_fields + [
        _list_field('ordering'),
        _list_field('public'),
        _list_field('icon'),
        _list_field(
            'functionalities',
            renderer=lambda themes: ', '.join(['{}={}'.format(f.name, f.value)
                                               for f in themes.functionalities]),
            filter_column=concat(Functionality.name, '=', Functionality.value)
        ),
        _list_field(
            'restricted_roles',
            renderer=lambda themes: ', '.join([r.name or '' for r in themes.restricted_roles]),
            filter_column=Role.name
        ),
        _list_field(
            'interfaces',
            renderer=lambda themes: ', '.join([i.name or '' for i in themes.interfaces]),
            filter_column=Interface.name
        )] + TreeItemViews._extra_list_fields

    _id_field = 'id'
    _model = Theme
    _base_schema = base_schema

    def _base_query(self, query=None):
        return super()._base_query(
            self._request.dbsession.query(Theme).distinct().
            outerjoin('interfaces').
            outerjoin('restricted_roles').
            outerjoin('functionalities').
            options(subqueryload('functionalities')).
            options(subqueryload('restricted_roles')).
            options(subqueryload('interfaces')))

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
