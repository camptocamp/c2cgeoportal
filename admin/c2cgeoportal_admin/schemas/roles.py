import colander
from c2cgeoform.ext.deform_ext import RelationCheckBoxListWidget
from c2cgeoform.schema import (
    GeoFormManyToManySchemaNode,
    manytomany_validator,
)
from c2cgeoportal_commons.models.main import Role


def roles_schema_node(name):
    return colander.SequenceSchema(
        GeoFormManyToManySchemaNode(Role),
        name=name,
        widget=RelationCheckBoxListWidget(
            Role,
            'id',
            'name',
            order_by='name',
            edit_url=lambda request, value: request.route_url(
                'c2cgeoform_item',
                table='roles',
                id=value
            )
        ),
        validator=manytomany_validator,
        missing=colander.drop
    )
