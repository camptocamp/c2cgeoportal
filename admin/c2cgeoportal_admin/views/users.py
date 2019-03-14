from functools import partial
from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_defaults
from pyramid.view import view_config

from passwordgenerator import pwgenerator

from sqlalchemy.orm import aliased, subqueryload
from c2cgeoform.schema import GeoFormSchemaNode
from c2cgeoform.views.abstract_views import AbstractViews, ListField
from deform.widget import FormWidget

from c2cgeoportal_commons.models.main import Role
from c2cgeoportal_commons.models.static import User
from c2cgeoportal_commons.lib.email_ import send_email_config
from c2cgeoportal_admin.schemas.roles import roles_schema_node

_list_field = partial(ListField, User)

base_schema = GeoFormSchemaNode(User, widget=FormWidget(fields_template='user_fields'))
base_schema.add(roles_schema_node('roles'))
base_schema.add_unique_validator(User.username, User.id)

settings_role = aliased(Role)


@view_defaults(match_param='table=users')
class UserViews(AbstractViews):
    _list_fields = [
        _list_field('id'),
        _list_field('username'),
        _list_field('email'),
        _list_field('last_login'),
        _list_field('expire_on'),
        _list_field('deactivated'),
        _list_field('settings_role',
                    renderer=lambda user: user.settings_role.name if user.settings_role else '',
                    sort_column=settings_role.name,
                    filter_column=settings_role.name),
        _list_field('roles',
                    renderer=lambda user: ', '.join([r.name or '' for r in user.roles]),
                    filter_column=Role.name),
    ]
    _id_field = 'id'
    _model = User
    _base_schema = base_schema

    def _base_query(self):
        return self._request.dbsession.query(User).distinct(). \
            outerjoin(settings_role, settings_role.id == User.settings_role_id). \
            outerjoin('roles'). \
            options(subqueryload('settings_role')). \
            options(subqueryload('roles'))

    @view_config(route_name='c2cgeoform_index',
                 renderer='../templates/index.jinja2')
    def index(self):
        return super().index()

    @view_config(route_name='c2cgeoform_grid',
                 renderer='fast_json')
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
        if self._is_new():
            response = super().save()

            if isinstance(response, HTTPFound):
                password = pwgenerator.generate()

                user = self._obj
                user.password = password
                user.is_password_changed = False
                user = self._request.dbsession.merge(user)
                self._request.dbsession.flush()

                send_email_config(
                    settings=self._request.registry.settings,
                    email_config_name='welcome_email',
                    email=user.email,
                    user=user.username,
                    password=password)

            return response

        return super().save()

    @view_config(route_name='c2cgeoform_item',
                 request_method='DELETE',
                 renderer='fast_json')
    def delete(self):
        return super().delete()

    @view_config(route_name='c2cgeoform_item_duplicate',
                 request_method='GET',
                 renderer='../templates/edit.jinja2')
    def duplicate(self):
        return super().duplicate()
