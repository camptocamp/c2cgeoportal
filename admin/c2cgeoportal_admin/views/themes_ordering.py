# Copyright (c) 2017-2024, Camptocamp SA
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


import colander
from c2cgeoform.schema import GeoFormSchemaNode
from c2cgeoform.views.abstract_views import AbstractViews, ObjectResponse, SaveResponse
from deform import ValidationFailure
from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config

from c2cgeoportal_admin import _
from c2cgeoportal_admin.schemas.treegroup import treeitem_edit_url
from c2cgeoportal_admin.widgets import ChildrenWidget, ChildWidget
from c2cgeoportal_commons.models.main import Theme, TreeItem


class ThemeOrderSchema(GeoFormSchemaNode):  # pylint: disable=abstract-method
    """The theme order schema."""

    def objectify(self, dict_, context=None):
        context = self.dbsession.query(Theme).get(dict_["id"])
        context = super().objectify(dict_, context)
        return context


@colander.deferred
def themes(node, kw):  # pylint: disable=unused-argument
    """Get some theme metadata."""
    query = kw["dbsession"].query(Theme).order_by(Theme.ordering, Theme.name)
    return [
        {"id": item.id, "label": item.name, "icon_class": f"icon-{item.item_type}", "group": "All"}
        for item in query
    ]


def themes_validator(node, cstruct):
    """Validate the theme."""
    for dict_ in cstruct:
        if not dict_["id"] in [item["id"] for item in node.candidates]:
            raise colander.Invalid(
                node,
                _("Value {} does not exist in table {}").format(dict_["id"], Theme.__tablename__),
            )


class ThemesOrderingSchema(colander.MappingSchema):  # type: ignore[misc]
    """The theme ordering schema."""

    themes = colander.SequenceSchema(
        ThemeOrderSchema(
            Theme,
            includes=["id", "ordering"],
            name="theme",
            widget=ChildWidget(
                input_name="id",
                model=TreeItem,
                label_field="name",
                icon_class=lambda item: f"icon-{item.item_type}",
                edit_url=treeitem_edit_url,
            ),
        ),
        name="themes",
        candidates=themes,
        validator=themes_validator,
        widget=ChildrenWidget(child_input_name="id", add_subitem=False, orderable=True),
    )


class ThemesOrdering(AbstractViews[ThemesOrderingSchema]):
    """The theme ordering admin view."""

    _base_schema = ThemesOrderingSchema()

    @view_config(route_name="layertree_ordering", request_method="GET", renderer="../templates/edit.jinja2")  # type: ignore[misc]
    def view(self) -> ObjectResponse:
        form = self._form()
        dict_ = {
            "themes": [
                form.schema["themes"].children[0].dictify(theme)
                for theme in self._request.dbsession.query(Theme).order_by(Theme.ordering)
            ]
        }
        return {
            "title": form.title,
            "form": form,
            "form_render_args": [dict_],
            "form_render_kwargs": {"request": self._request, "actions": []},
            "deform_dependencies": form.get_widget_resources(),
        }

    @view_config(route_name="layertree_ordering", request_method="POST", renderer="../templates/edit.jinja2")  # type: ignore[misc]
    def save(self) -> SaveResponse:
        try:
            form = self._form()
            form_data = self._request.POST.items()
            _appstruct = form.validate(form_data)
            with self._request.dbsession.no_autoflush:
                for dict_ in _appstruct["themes"]:
                    obj = form.schema["themes"].children[0].objectify(dict_)
                    self._request.dbsession.merge(obj)
            self._request.dbsession.flush()
            return HTTPFound(self._request.route_url("layertree"))
        except ValidationFailure as e:
            # FIXME see https://github.com/Pylons/deform/pull/243
            self._populate_widgets(form.schema)
            return {
                "title": form.title,
                "form": e,
                "form_render_args": [],
                "form_render_kwargs": {"request": self._request, "actions": []},
                "deform_dependencies": form.get_widget_resources(),
            }
