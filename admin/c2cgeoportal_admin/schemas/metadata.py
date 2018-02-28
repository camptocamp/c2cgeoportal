import json
from json.decoder import JSONDecodeError
import colander
from deform.widget import MappingWidget, SelectWidget, SequenceWidget, TextAreaWidget
from c2cgeoform.schema import GeoFormSchemaNode
from c2cgeoportal_commons.models.main import Metadata
from c2cgeoportal_admin import _


@colander.deferred
def metadata_types(node, kw):  # pylint: disable=unused-argument
    return {
        m['name']: m.get('type', 'string')
        for m in kw['request'].registry.settings['admin_interface']['available_metadata']
    }


@colander.deferred
def metadata_name_widget(node, kw):  # pylint: disable=unused-argument
    return SelectWidget(
        values=[
            (m['name'], m['name'])
            for m in sorted(
                kw['request'].registry.settings['admin_interface']['available_metadata'],
                key=lambda m: m['name'])
        ]
    )


def json_validator(node, value):
    try:
        json.loads(value)
    except JSONDecodeError as e:
        raise colander.Invalid(node, _('Parser report: "{}"').format(str(e)))


@colander.deferred
def color_validator(node, kw):  # pylint: disable=unused-argument
    color_val = kw['request'].registry.settings['admin_interface']['color_validator']
    return colander.Regex(color_val['regex'], msg=_(color_val['msg']))


class MetadataSchemaNode(GeoFormSchemaNode):

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)

        self.available_types = []

        self._add_value_node('string', colander.String())
        self._add_value_node('liste', colander.String())
        self._add_value_node('boolean', colander.Boolean())
        self._add_value_node('int', colander.Int())
        self._add_value_node('float', colander.Float())
        self._add_value_node('url', colander.String(), validator=colander.url)
        self._add_value_node(
            'json',
            colander.String(),
            widget=TextAreaWidget(rows=10),
            validator=json_validator),
        self._add_value_node(
            'color',
            colander.String(),
            validator=self.color_validator)

    def _add_value_node(self, type_name, colander_type, **kw):
        self.add_before(
            'description',
            colander.SchemaNode(
                colander_type,
                name=type_name,
                missing=colander.null,
                **kw))
        self.available_types.append(type_name)

    def objectify(self, dict_, context=None):
        # depending on the type get the value from the right widget
        dict_['value'] = dict_[self._ui_type(dict_['name'])]
        return super().objectify(dict_, context)

    def dictify(self, obj):
        dict_ = super().dictify(obj)
        value = obj.value or colander.null
        # depending on the type set the value in the right widget
        dict_[self._ui_type(obj.name)] = value
        return dict_

    def _ui_type(self, metadata_name):
        metadata_type = self.metadata_types.get(metadata_name, 'string')
        return metadata_type if metadata_type in self.available_types else 'string'


metadatas_schema_node = colander.SequenceSchema(
    MetadataSchemaNode(
        Metadata,
        name='metadata',
        metadata_types=metadata_types,
        color_validator=color_validator,
        widget=MappingWidget(template='metadata'),
        overrides={
            'name': {
                'widget': metadata_name_widget
            }
        }
    ),
    name='metadatas',
    metadata_types=metadata_types,
    widget=SequenceWidget(
        template='metadatas',
        category='structural')
)
