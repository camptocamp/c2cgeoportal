import colander
from c2cgeoform.ext.deform_ext import RelationCheckBoxListWidget
from c2cgeoform.schema import (
    GeoFormManyToManySchemaNode,
    manytomany_validator,
)
from c2cgeoportal_commons.models.main import RestrictionArea

restrictionareas_schema_node = colander.SequenceSchema(
    GeoFormManyToManySchemaNode(RestrictionArea),
    name='restrictionareas',
    widget=RelationCheckBoxListWidget(
        RestrictionArea,
        'id',
        'name',
        order_by='name'
    ),
    validator=manytomany_validator
)
