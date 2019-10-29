from c2cgeoform.schema import GeoFormSchemaNode
import colander
from deform.widget import MappingWidget, SequenceWidget

from c2cgeoportal_admin import _
from c2cgeoportal_commons.models.main import Dimension

dimensions_schema_node = colander.SequenceSchema(
    GeoFormSchemaNode(Dimension, name="dimension", widget=MappingWidget(template="dimension")),
    name="dimensions",
    title=_("Dimensions"),
    widget=SequenceWidget(category="structural", template="dimensions"),
)
