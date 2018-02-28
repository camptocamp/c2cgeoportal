import colander
import deform

from functools import partial

from c2cgeoportal_admin.schemas.treegroup import base_deferred_parent_id_validator


# Used for the creation of a new layer/layergroup from the layertree
def parent_id_node(model):
    return colander.SchemaNode(
        colander.Integer(),
        name='parent_id',
        missing=colander.drop,
        validator=colander.deferred(partial(base_deferred_parent_id_validator, model=model)),
        widget=deform.widget.HiddenWidget()
    )
