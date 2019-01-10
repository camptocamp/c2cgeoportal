Extend the data model
---------------------

The Data model can be extended in the file ``geoportal/<package>_geoportal/models.py``.

For example to add some user details, including a link to a new class named "Title",
add to ``geoportal/<package>_geoportal/models.py``:

.. code:: python

    # Used to hide the original user in the admin interface
    User.__acl__ = [DENY_ALL]

    class UserDetail(User):
        __tablename__ = 'userdetail'
        __table_args__ = {'schema': _schema}
        __acl__ = [
            (Allow, Authenticated, ALL_PERMISSIONS),
        ]
        __mapper_args__ = {'polymorphic_identity': 'detailed'}
        __colanderalchemy_config__ = {
            'title': _('User detail'),
            'plural': _('User details')
        }
        id = Column(
            types.Integer,
            ForeignKey(_schema + '.user.id'),
            primary_key=True
        )

        phone = Column(
            types.Unicode,
            nullable=False,
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
        __acl__ = [
            (Allow, Authenticated, ALL_PERMISSIONS),
        ]
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
* ``geoportal/<package>_geoportal/admin/view/__init__.py``:

Now, create a file ``geoportal/<package>_geoportal/admin/views/userdetail.py`` as follows:

.. code:: python

    from <package>_geoportal.models import UserDetail
    from functools import partial
    from pyramid.view import view_defaults
    from pyramid.view import view_config

    from c2cgeoform.schema import GeoFormSchemaNode
    from c2cgeoform.views.abstract_views import AbstractViews
    from c2cgeoform.views.abstract_views import ListField


    base_schema = GeoFormSchemaNode(UserDetail)

    @view_defaults(match_param='table=userdetail')
    class LuxDownloadUrlViews(AbstractViews):
        _list_fields = [
            _list_field('id'),
            _list_field('phone'),
            _list_field('title'),
        ]
        _id_field = 'id'
        _model = UserDetail
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

And now the file ``geoportal/<package>_geoportal/admin/views/title.py``:

.. code:: python

    from <package>_geoportal.models import Title
    from functools import partial
    from pyramid.view import view_defaults
    from pyramid.view import view_config

    from c2cgeoform.schema import GeoFormSchemaNode
    from c2cgeoform.views.abstract_views import AbstractViews
    from c2cgeoform.views.abstract_views import ListField


    base_schema = GeoFormSchemaNode(UserDetail)

    @view_defaults(match_param='table=title')
    class LuxDownloadUrlViews(AbstractViews):
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

And finally in ``geoportal/<package>_geoportal/__init__.py`` replace ``config.scan()`` by:

.. code:: python

    # Add custom table in admin interface, that means re-add all normal table
    from c2cgeoform.routes import register_models
    from c2cgeoportal_commons.models.main import (
        Role, LayerWMS, LayerWMTS, Theme, LayerGroup, Interface, OGCServer,
        Functionality, RestrictionArea)
    from c2cgeoportal_commons.models.static import User
    from c2cgeoportal_admin import PermissionSetter
    from <package>_geoportal.models import UserDetail, Title

    register_models(config, (
        ('themes', Theme),
        ('layer_groups', LayerGroup),
        ('layers_wms', LayerWMS),
        ('layers_wmts', LayerWMTS),
        ('ogc_servers', OGCServer),
        ('restriction_areas', RestrictionArea),
        ('users', User),
        ('roles', Role),
        ('functionalities', Functionality),
        ('interfaces', Interface),
        ('userdetail', UserDetail),
        ('title', Title),
    ))

    with PermissionSetter(config):
        # Scan view decorator for adding routes
        config.scan('<package>.admin.views')
    config.scan(ignore='<package>.admin.views')
