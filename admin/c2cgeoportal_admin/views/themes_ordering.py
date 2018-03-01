from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound

import colander
from c2cgeoform.schema import GeoFormSchemaNode
from c2cgeoform.views.abstract_views import AbstractViews
from deform import ValidationFailure
from sqlalchemy.sql.expression import literal_column

from c2cgeoportal_commons.models.main import Theme

from c2cgeoportal_admin import _
from c2cgeoportal_admin.widgets import ThemeOrderWidget, ChildrenWidget


class ThemeOrderSchema(GeoFormSchemaNode):

    def objectify(self, dict_, context=None):
        context = self.dbsession.query(Theme).get(dict_['id'])
        context = super().objectify(dict_, context)
        return context


@colander.deferred
def treeitems(node, kw):  # pylint: disable=unused-argument
    return kw['dbsession'].query(Theme, literal_column('0')). \
        order_by(Theme.ordering, Theme.name)


def themes_validator(node, cstruct):
    for dict_ in cstruct:
        if not dict_['id'] in [item.id for item, dummy in node.treeitems]:
            raise colander.Invalid(
                node,
                _('Value {} does not exist in table {}').
                format(dict_['treeitem_id'], Theme.__tablename__))


class ThemesOrderingSchema(colander.MappingSchema):
    themes = colander.SequenceSchema(
        ThemeOrderSchema(
            Theme,
            includes=['id', 'ordering'],
            name='theme',
            widget=ThemeOrderWidget()
        ),
        name='themes',
        treeitems=treeitems,
        validator=themes_validator,
        widget=ChildrenWidget(add_subitem=False, category='structural')
    )


class ThemesOrdering(AbstractViews):

    _base_schema = ThemesOrderingSchema()

    @view_config(route_name='layertree_ordering',
                 request_method='GET',
                 renderer='../templates/edit.jinja2')
    def edit(self):
        form = self._form()
        dict_ = {
            'themes': [form.schema['themes'].children[0].dictify(theme)
                       for theme, dummy in form.schema['themes'].treeitems]
        }
        rendered = form.render(dict_,
                               request=self._request,
                               actions=[])
        return {
            'form': rendered,
            'deform_dependencies': form.get_widget_resources()
        }

    @view_config(route_name='layertree_ordering',
                 request_method='POST',
                 renderer='../templates/edit.jinja2')
    def save(self):
        try:
            form = self._form()
            form_data = self._request.POST.items()
            _appstruct = form.validate(form_data)
            with self._request.dbsession.no_autoflush:
                for dict_ in _appstruct['themes']:
                    obj = form.schema['themes'].children[0].objectify(dict_)
                    self._request.dbsession.merge(obj)
            self._request.dbsession.flush()
            return HTTPFound(
                self._request.route_url(
                    'layertree'))
        except ValidationFailure as e:
            # FIXME see https://github.com/Pylons/deform/pull/243
            self._populate_widgets(form.schema)
            rendered = e.field.widget.serialize(
                e.field,
                e.cstruct,
                request=self._request,
                actions=[])
            return {
                'form': rendered,
                'deform_dependencies': form.get_widget_resources()
            }
