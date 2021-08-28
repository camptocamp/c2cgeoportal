import colander
from deform.widget import MappingWidget, SequenceWidget
from c2cgeoform.schema import GeoFormSchemaNode
from c2cgeoportal_commons.models.main import Dimension
from c2cgeoportal_admin import _


def dimensions_schema_node(prop):
    return colander.SequenceSchema(
        GeoFormSchemaNode(
            Dimension,
            name='dimension',
            widget=MappingWidget(template='dimension')),
        name=prop.key,
        title=prop.info['colanderalchemy']['title'],
        description=prop.info['colanderalchemy']['description'],
        widget=SequenceWidget(category='structural', template='dimensions'),
    )
