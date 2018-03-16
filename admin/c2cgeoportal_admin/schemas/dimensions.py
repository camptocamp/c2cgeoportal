import colander
from deform.widget import MappingWidget, SequenceWidget
from c2cgeoform.schema import GeoFormSchemaNode
from c2cgeoportal_commons.models.main import Dimension
from c2cgeoportal_admin import _


dimensions_schema_node = colander.SequenceSchema(
    GeoFormSchemaNode(
        Dimension,
        name='dimension',
        widget=MappingWidget(template='dimension'),
    ),
    name='dimensions',
    title=_('Dimensions'),
    widget=SequenceWidget(category='structural', template='dimensions')
)
