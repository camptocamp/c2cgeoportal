import colander
from deform.widget import MappingWidget
from c2cgeoform.schema import GeoFormSchemaNode
from c2cgeoportal_commons.models.main import Dimension


dimensions_schema_node = colander.SequenceSchema(
    GeoFormSchemaNode(
        Dimension,
        name='dimension',
        widget=MappingWidget(template='dimension'),
    ),
    name='dimensions',
)
