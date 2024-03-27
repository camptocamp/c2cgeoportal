Extend the data model
---------------------

.. note::

    Extending the data model is not possible in the simple application mode.

The data model can be extended in the file ``geoportal/<package>_geoportal/models.py``.

For example, to add some user details, including a link to a new class named "Title",
add to ``geoportal/<package>_geoportal/models.py``:

.. code:: python

    from deform.widget import HiddenWidget
    from sqlalchemy import Column, ForeignKey, types
    from sqlalchemy.orm import backref, relationship

    from c2cgeoportal_commons.models.static import User, _schema


    class UserDetail(User):
        __tablename__ = 'userdetail'
        __table_args__ = {'schema': _schema}
        __mapper_args__ = {'polymorphic_identity': 'detailed'}
        __colanderalchemy_config__ = {
            'title': _('User detail'),
            'plural': _('User details')
        }
        id = Column(
            types.Integer,
            ForeignKey(_schema + '.user.id'),
            primary_key=True,
            info={
                "colanderalchemy": {
                    "missing": None,
                    "widget": HiddenWidget()
                }
            }
        )

        phone = Column(
            types.Unicode,
            info={
                'colanderalchemy': {
                    'title': _('Phone')
                }
            }
        )

        # title
        title_id = Column(Integer, ForeignKey(_schema + '.title.id'), nullable=False)
        title = relationship("Title", backref=backref('users'), info={
            'colanderalchemy': {
                'title': _('Title')
            }
        })


    class Title(Base):
        __tablename__ = 'title'
        __table_args__ = {'schema': _schema}
        __colanderalchemy_config__ = {
            'title': _('Title'),
            'plural': _('Titles')
        }
        id = Column(types.Integer, primary_key=True)
        name = Column(types.Unicode, nullable=False, info={
            'colanderalchemy': {
                'title': _('Name')
            }
        })

Now you need to extend the administration user interface.
For this, first ensure that the following files exist (if needed, create them as empty files):

* ``geoportal/<package>_geoportal/admin/__init__.py``:
* ``geoportal/<package>_geoportal/admin/views/__init__.py``:

Now, create a file ``geoportal/<package>_geoportal/admin/views/userdetail.py`` as follows:

.. code:: python

    from functools import partial

    from <package>_geoportal.models import UserDetail
    from c2cgeoform.schema import GeoFormSchemaNode
    from c2cgeoform.views.abstract_views import ListField
    from deform.widget import FormWidget
    from pyramid.view import view_config, view_defaults
    from sqlalchemy.orm import aliased, subqueryload

    from c2cgeoportal_admin.schemas.roles import roles_schema_node
    from c2cgeoportal_admin.views.users import UserViews
    from c2cgeoportal_commons.models.main import Role
    from c2cgeoportal_commons.models.static import User


    _list_field = partial(ListField, UserDetail)

    base_schema = GeoFormSchemaNode(UserDetail, widget=FormWidget(fields_template="user_fields"))
    base_schema.add(roles_schema_node(User.roles))
    base_schema.add_unique_validator(UserDetail.username, UserDetail.id)

    settings_role = aliased(Role)


    @view_defaults(match_param='table=userdetails')
    class UserDetailViews(UserViews):
        _list_fields = [
            _list_field('id'),
            _list_field('username'),
            _list_field('title'),
            _list_field('email'),
            _list_field('last_login'),
            _list_field('expire_on'),
            _list_field('deactivated'),
            _list_field('phone'),
            _list_field(
                "settings_role",
                renderer=lambda user: user.settings_role.name if user.settings_role else "",
                sort_column=settings_role.name,
                filter_column=settings_role.name,
            ),
            _list_field(
                "roles",
                renderer=lambda user: ", ".join([r.name or "" for r in user.roles]),
                filter_column=Role.name,
            ),
        ]
        _id_field = 'id'
        _model = UserDetail
        _base_schema = base_schema

        def _base_query(self):
            return (
                self._request.dbsession.query(UserDetail)
                .distinct()
                .outerjoin(settings_role, settings_role.id == UserDetail.settings_role_id)
                .outerjoin(User.roles)
                .options(subqueryload(User.settings_role))
                .options(subqueryload(User.roles))
            )

        @view_config(
            route_name='c2cgeoform_index',
            renderer='./templates/index.jinja2'
        )
        def index(self):
            return super().index()

        @view_config(
            route_name='c2cgeoform_grid',
            renderer='fast_json'
        )
        def grid(self):
            return super().grid()

        @view_config(
            route_name='c2cgeoform_item',
            request_method='GET',
            renderer='./templates/edit.jinja2'
        )
        def view(self):
            return super().edit()

        @view_config(
            route_name='c2cgeoform_item',
            request_method='POST',
            renderer='./templates/edit.jinja2'
        )
        def save(self):
            return super().save()

        @view_config(
            route_name='c2cgeoform_item',
            request_method='DELETE',
            renderer='fast_json'
        )
        def delete(self):
            return super().delete()

        @view_config(
            route_name='c2cgeoform_item_duplicate',
            request_method='GET',
            renderer='./templates/edit.jinja2'
        )
        def duplicate(self):
            return super().duplicate()

And now the file ``geoportal/<package>_geoportal/admin/views/title.py``:

.. code:: python

    from functools import partial

    from <package>_geoportal.models import Title
    from c2cgeoform.schema import GeoFormSchemaNode
    from c2cgeoform.views.abstract_views import AbstractViews, ListField
    from pyramid.view import view_config, view_defaults


    base_schema = GeoFormSchemaNode(Title)
    _list_field = partial(ListField, Title)


    @view_defaults(match_param='table=titles')
    class TitleViews(AbstractViews):
        _list_fields = [
            _list_field('id'),
            _list_field('name'),
        ]
        _id_field = 'id'
        _model = Title
        _base_schema = base_schema

        @view_config(
            route_name='c2cgeoform_index',
            renderer='./templates/index.jinja2'
        )
        def index(self):
            return super().index()

        @view_config(
            route_name='c2cgeoform_grid',
            renderer='fast_json'
        )
        def grid(self):
            return super().grid()

        @view_config(
            route_name='c2cgeoform_item',
            request_method='GET',
            renderer='./templates/edit.jinja2'
        )
        def view(self):
            return super().edit()

        @view_config(
            route_name='c2cgeoform_item',
            request_method='POST',
            renderer='./templates/edit.jinja2'
        )
        def save(self):
            return super().save()

        @view_config(
            route_name='c2cgeoform_item',
            request_method='DELETE',
            renderer='fast_json'
        )
        def delete(self):
            return super().delete()

        @view_config(
            route_name='c2cgeoform_item_duplicate',
            request_method='GET',
            renderer='./templates/edit.jinja2'
        )
        def duplicate(self):
            return super().duplicate()

Change the User page in the admin, add it in your configuration ``geoportal/vars.yaml``:

.. code:: yaml

   vars:
       ...
       admin_interface:
           ...
           exclude_pages:
             - users
             - roles
             - functionalities
             - interfaces
           include_pages:
             - url_path: userdetails
               model: <package>_geoportal.models.UserDetail
             - url_path: titles
               model: <package>_geoportal.models.Title
             - url_path: roles
               model: c2cgeoportal_commons.models.main.Role
             - url_path: functionalities
               model: c2cgeoportal_commons.models.main.Functionality
             - url_path: interfaces
               model: c2cgeoportal_commons.models.main.Interface

And finally in ``geoportal/<package>_geoportal/__init__.py`` replace ``config.scan()`` by:

.. code:: python

    from c2cgeoportal_admin import PermissionSetter

    with PermissionSetter(config):
        # Scan view decorator for adding routes
        config.scan('<package>_geoportal.admin.views')
    config.scan(ignore='<package>_geoportal.admin.views')

Build and run the application:

.. prompt:: bash

   ./build <args>
   docker-compose up -d

Get and run the SQL command to create the tables:

Run Python console:

.. prompt:: bash

   docker-compose exec geoportal python3

Execute the following code:

.. code:: python

   import sqlalchemy
   from c2c.template.config import config

   import c2cgeoportal_commons.models

   config.init('/etc/geomapfish/config.yaml')
   engine = sqlalchemy.engine_from_config(config.get_config(), 'sqlalchemy.')
   c2cgeoportal_commons.models.Base.metadata.bind = engine

   from <package>_geoportal.models import Title, UserDetail
   from sqlalchemy.schema import CreateTable

   print(CreateTable(Title.__table__))
   print(CreateTable(UserDetail.__table__))

If the generated SQL looks good, do in the same Python console to effectively create the tables:

.. prompt:: python

   Title.__table__.create()
   UserDetail.__table__.create()
