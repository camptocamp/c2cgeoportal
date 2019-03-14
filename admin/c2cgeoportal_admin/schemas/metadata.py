import json
import colander
from deform.widget import MappingWidget, SelectWidget, SequenceWidget, TextAreaWidget
from c2cgeoform.schema import GeoFormSchemaNode
from c2cgeoportal_commons.lib.validators import url
from c2cgeoportal_commons.models.main import Metadata
from c2cgeoportal_admin import _


@colander.deferred
def metadata_definitions(node, kw):  # pylint: disable=unused-argument
    return {
        m['name']: m
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
    except ValueError as e:
        raise colander.Invalid(node, _('Parser report: "{}"').format(str(e)))


def regex_validator(node, value):
    definition = node.metadata_definitions[value['name']]
    if definition.get('type', 'string') == 'regex':
        validator = colander.Regex(definition['regex'], msg=_(definition['error_message']))
        try:
            validator(node['string'], value['string'])
        except colander.Invalid as e:
            error = colander.Invalid(node)
            error.add(e, node.children.index(node['string']))
            raise error


class MetadataSchemaNode(GeoFormSchemaNode):

    metadata_definitions = None

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)

        self.available_types = []

        self._add_value_node('string', colander.String())
        self._add_value_node('liste', colander.String())
        self._add_value_node('boolean', colander.Boolean())
        self._add_value_node('int', colander.Int())
        self._add_value_node('float', colander.Float())
        self._add_value_node('url', colander.String(), validator=url)
        self._add_value_node(
            'json',
            colander.String(),
            widget=TextAreaWidget(rows=10),
            validator=json_validator)

    def _add_value_node(self, type_name, colander_type, **kw):
        self.add_before(
            'description',
            colander.SchemaNode(
                colander_type,
                name=type_name,
                title=_('Value'),
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
        # pylint: disable=unsubscriptable-object
        metadata_type = self.metadata_definitions[metadata_name].get('type', 'string')
        return metadata_type if metadata_type in self.available_types else 'string'


metadatas_schema_node = colander.SequenceSchema(
    MetadataSchemaNode(
        Metadata,
        name='metadata',
        metadata_definitions=metadata_definitions,
        validator=regex_validator,
        widget=MappingWidget(template='metadata'),
        overrides={
            'name': {
                'widget': metadata_name_widget
            }
        }
    ),
    name='metadatas',
    title=_('Metadatas'),
    metadata_definitions=metadata_definitions,
    widget=SequenceWidget(
        template='metadatas',
        category='structural')
)
