import colander
from sqlalchemy import select
from sqlalchemy.sql.functions import concat
from c2cgeoform.ext.deform_ext import RelationCheckBoxListWidget
from c2cgeoform.schema import (
    GeoFormManyToManySchemaNode,
    manytomany_validator,
)
from c2cgeoportal_commons.models.main import Functionality


def functionalities_schema_node(prop):
    return colander.SequenceSchema(
        GeoFormManyToManySchemaNode(Functionality),
        name=prop.key,
        title=prop.info['colanderalchemy']['title'],
        description=prop.info['colanderalchemy'].get('description'),
        widget=RelationCheckBoxListWidget(
            select(
                [
                    Functionality.id,
                    concat(Functionality.name, '=', Functionality.value).label('label'),
                ]
            ).alias('functionality_labels'),
            'id',
            'label',
            order_by='label',
            edit_url=lambda request, value: request.route_url(
                'c2cgeoform_item', table='functionalities', id=value
            ),
        ),
        validator=manytomany_validator,
        missing=colander.drop,
    )
