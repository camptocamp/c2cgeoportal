import colander
from c2cgeoform.ext.deform_ext import RelationCheckBoxListWidget
from c2cgeoform.schema import (
    GeoFormManyToManySchemaNode,
    manytomany_validator,
)
from c2cgeoportal_commons.models.main import Interface
from c2cgeoportal_admin import _

interfaces_schema_node = colander.SequenceSchema(
    GeoFormManyToManySchemaNode(Interface),
    name='interfaces',
    title=_('Interfaces'),
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
    validator=manytomany_validator,
    missing=colander.drop
)
