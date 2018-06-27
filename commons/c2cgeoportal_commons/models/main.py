# -*- coding: utf-8 -*-

# Copyright (c) 2011-2017, Camptocamp SA
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# The views and conclusions contained in the software and documentation are those
# of the authors and should not be interpreted as representing official policies,
# either expressed or implied, of the FreeBSD Project.


import logging
from typing import List, Optional, Any
from typing import Union, Tuple, Dict  # noqa, pylint: disable=unused-import

from papyrus.geo_interface import GeoInterface
from sqlalchemy import ForeignKey, Table, event
from sqlalchemy.types import Integer, Boolean, Unicode, Float, String, \
    Enum, UserDefinedType
from sqlalchemy import UniqueConstraint, Column
from sqlalchemy.schema import Index
from sqlalchemy.orm import relationship, backref, Session
from geoalchemy2 import Geometry
from geoalchemy2.shape import to_shape
from c2cwsgiutils import broadcast

import zope.event
import colander
from deform.widget import HiddenWidget, SelectWidget, TextAreaWidget
from c2cgeoform.ext import colander_ext, deform_ext

from c2cgeoportal_commons.config import config
from c2cgeoportal_commons.models import Base, _
from c2cgeoportal_commons.models.sqlalchemy import JSONEncodedDict


LOG = logging.getLogger(__name__)

_schema = config['schema']  # type: str
_srid = config['srid']  # type: int


class InvalidateCacheEvent:
    pass


def cache_invalidate_cb(*args: List[Any]) -> None:
    _cache_invalidate_cb()


@broadcast.decorator()
def _cache_invalidate_cb() -> None:
    zope.event.notify(InvalidateCacheEvent())


class TsVector(UserDefinedType):
    """ A custom type for PostgreSQL's tsvector type. """

    def get_col_spec(self) -> str:  # pragma: no cover
        return 'TSVECTOR'


class FullTextSearch(GeoInterface, Base):
    __tablename__ = 'tsearch'
    __table_args__ = (
        Index('tsearch_ts_idx', 'ts', postgresql_using='gin'),
        {'schema': _schema}
    )

    id = Column(Integer, primary_key=True)
    label = Column(Unicode)
    layer_name = Column(Unicode)  # Deprecated in v2
    role_id = Column(Integer, ForeignKey(_schema + '.role.id'), nullable=True)
    role = relationship('Role')
    interface_id = Column(Integer, ForeignKey(_schema + '.interface.id'), nullable=True)
    interface = relationship('Interface')
    lang = Column(String(2), nullable=True)
    public = Column(Boolean, server_default='true')
    ts = Column(TsVector)
    the_geom = Column(Geometry('GEOMETRY', srid=_srid))
    params = Column(JSONEncodedDict, nullable=True)
    actions = Column(JSONEncodedDict, nullable=True)
    from_theme = Column(Boolean, server_default='false')


class Functionality(Base):
    __tablename__ = 'functionality'
    __table_args__ = {'schema': _schema}
    __colanderalchemy_config__ = {
        'title': _('Functionality'),
        'plural': _('Functionalities')
    }

    __c2cgeoform_config__ = {
        'duplicate': True
    }

    id = Column(Integer, primary_key=True, info={
        'colanderalchemy': {
            'widget': HiddenWidget()
        }
    })
    name = Column(Unicode, nullable=False, info={
        'colanderalchemy': {'title': _('Name')}
    })
    description = Column(Unicode, info={
        'colanderalchemy': {'title': _('Description')}
    })
    value = Column(Unicode, nullable=False, info={
        'colanderalchemy': {'title': _('Value')}
    })

    def __init__(self, name: str='', value: str='', description: str='') -> None:
        self.name = name
        self.value = value
        self.description = description

    def __unicode__(self) -> str:
        return '{0!s} - {1!s}'.format(self.name or '', self.value or '')  # pragma: no cover


event.listen(Functionality, 'after_update', cache_invalidate_cb)
event.listen(Functionality, 'after_delete', cache_invalidate_cb)


# association table role <> functionality
role_functionality = Table(
    'role_functionality', Base.metadata,
    Column('role_id', Integer, ForeignKey(_schema + '.role.id'), primary_key=True),
    Column('functionality_id', Integer, ForeignKey(_schema + '.functionality.id'), primary_key=True),
    schema=_schema
)

# association table theme <> functionality
theme_functionality = Table(
    'theme_functionality', Base.metadata,
    Column('theme_id', Integer, ForeignKey(_schema + '.theme.id'), primary_key=True),
    Column('functionality_id', Integer, ForeignKey(_schema + '.functionality.id'), primary_key=True),
    schema=_schema
)


class Role(Base):
    __tablename__ = 'role'
    __table_args__ = {'schema': _schema}
    __colanderalchemy_config__ = {
        'title': _('Role'),
        'plural': _('Roles')
    }
    __c2cgeoform_config__ = {
        'duplicate': True
    }

    id = Column(Integer, primary_key=True, info={
        'colanderalchemy': {
            'widget': HiddenWidget()
        }
    })
    name = Column(Unicode, unique=True, nullable=False, info={
        'colanderalchemy': {
            'title': _('Name')
        }
    })
    description = Column(Unicode, info={
        'colanderalchemy': {
            'title': _('Description')
        }
    })
    extent = Column(Geometry('POLYGON', srid=_srid), info={
        'colanderalchemy': {
            'typ': colander_ext.Geometry('POLYGON', srid=_srid, map_srid=3857)
        }
    })

    # functionality
    functionalities = relationship(
        'Functionality', secondary=role_functionality,
        cascade='save-update,merge,refresh-expire',
        info={
            'colanderalchemy': {
                'exclude': True,
                'title': _('Functionalities')
            }
        }
    )

    def __init__(
        self, name: str='', description: str='',
        functionalities: List[Functionality]=None, extent: Geometry=None
    ) -> None:
        if functionalities is None:
            functionalities = []
        self.name = name
        self.functionalities = functionalities
        self.extent = extent
        self.description = description

    def __unicode__(self) -> str:
        return self.name or ''  # pragma: no cover

    @property
    def bounds(self) -> None:
        if self.extent is None:
            return None
        return to_shape(self.extent).bounds


event.listen(Role.functionalities, 'set', cache_invalidate_cb)
event.listen(Role.functionalities, 'append', cache_invalidate_cb)
event.listen(Role.functionalities, 'remove', cache_invalidate_cb)


class TreeItem(Base):
    __tablename__ = 'treeitem'
    __table_args__ = (
        UniqueConstraint('type', 'name'),
        {'schema': _schema},
    )  # type: Union[Tuple, Dict[str, Any]]
    item_type = Column('type', String(10), nullable=False, info={
        'colanderalchemy': {
            'exclude': True
        }})
    __mapper_args__ = {'polymorphic_on': item_type}

    id = Column(Integer, primary_key=True)
    name = Column(Unicode, nullable=False, info={
        'colanderalchemy': {
            'title': _('Name')
        }})
    metadata_url = Column(Unicode, info={
        'colanderalchemy': {
            'title': _('Metadata URL')
        }})  # should not be used in V2
    description = Column(Unicode, info={
        'colanderalchemy': {
            'title': _('Description')
        }})

    @property
    # Better: def parents(self) -> List[TreeGroup]:  # pragma: no cover
    def parents(self) -> List['TreeItem']:  # pragma: no cover
        return [c.group for c in self.parents_relation]

    def is_in_interface(self, name: str) -> bool:
        if not hasattr(self, 'interfaces'):  # pragma: no cover
            return False

        for interface in self.interfaces:
            if interface.name == name:
                return True

        return False

    def get_metadatas(self, name: str) -> List['Metadata']:  # pragma: no cover
        return [metadata for metadata in self.metadatas if metadata.name == name]

    def __init__(self, name: str='') -> None:
        self.name = name


event.listen(TreeItem, 'after_insert', cache_invalidate_cb, propagate=True)
event.listen(TreeItem, 'after_update', cache_invalidate_cb, propagate=True)
event.listen(TreeItem, 'after_delete', cache_invalidate_cb, propagate=True)


# association table TreeGroup <> TreeItem
class LayergroupTreeitem(Base):
    __tablename__ = 'layergroup_treeitem'
    __table_args__ = {'schema': _schema}

    # required by formalchemy
    id = Column(Integer, primary_key=True, info={
        'colanderalchemy': {'widget': HiddenWidget()}}
    )
    description = Column(Unicode, info={'colanderalchemy': {'exclude': True}})
    treegroup_id = Column(Integer, ForeignKey(_schema + '.treegroup.id'), info={
        'colanderalchemy': {'exclude': True}}
    )
    treegroup = relationship(
        'TreeGroup',
        backref=backref(
            'children_relation',
            order_by='LayergroupTreeitem.ordering',
            cascade='save-update,merge,delete,delete-orphan,expunge',
            info={
                'colanderalchemy': {
                    'title': _('Children'),
                    'exclude': True
                },
            }
        ),
        primaryjoin='LayergroupTreeitem.treegroup_id==TreeGroup.id',
        info={
            'colanderalchemy': {'exclude': True},
            'c2cgeoform': {'duplicate': False}
        }
    )
    treeitem_id = Column(Integer, ForeignKey(_schema + '.treeitem.id'), info={
        'colanderalchemy': {'widget': HiddenWidget()}}
    )
    treeitem = relationship(
        'TreeItem',
        backref=backref(
            'parents_relation',
            cascade='save-update,merge,delete,delete-orphan',
            info={
                'colanderalchemy': {
                    'title': _('Parents'),
                    'exclude': True
                },
                'c2cgeoform': {
                    'duplicate': False
                }
            }
        ),
        primaryjoin='LayergroupTreeitem.treeitem_id==TreeItem.id',
        info={
            'colanderalchemy': {'exclude': True},
            'c2cgeoform': {'duplicate': False}
        }
    )
    ordering = Column(Integer, info={
        'colanderalchemy': {'widget': HiddenWidget()}}
    )

    def __init__(self, group: 'TreeGroup'=None, item: TreeItem=None, ordering: int=0) -> None:
        self.treegroup = group
        self.treeitem = item
        self.ordering = ordering


event.listen(LayergroupTreeitem, 'after_insert', cache_invalidate_cb, propagate=True)
event.listen(LayergroupTreeitem, 'after_update', cache_invalidate_cb, propagate=True)
event.listen(LayergroupTreeitem, 'after_delete', cache_invalidate_cb, propagate=True)


class TreeGroup(TreeItem):
    __tablename__ = 'treegroup'
    __table_args__ = {'schema': _schema}
    __mapper_args__ = {
        'polymorphic_identity': 'treegroup'  # needed for _identity_class
    }

    id = Column(Integer, ForeignKey(_schema + '.treeitem.id'), primary_key=True)

    def _get_children(self) -> List[TreeItem]:
        return [c.treeitem for c in self.children_relation]

    def _set_children(self, children: List[TreeItem], order: bool=False) -> None:
        for child in self.children_relation:
            if child.treeitem not in children:
                child.treeitem = None
                child.treegroup = None
        if order is True:  # pragma: nocover
            for index, child in enumerate(children):
                current = [c for c in self.children_relation if c.treeitem == child]
                if len(current) == 1:
                    current[0].ordering = index * 10
                else:
                    LayergroupTreeitem(self, child, index * 10)
            self.children_relation.sort(key=lambda child: child.ordering)
        else:
            current_item = [child.treeitem for child in self.children_relation]
            for index, item in enumerate(children):
                if item not in current_item:
                    LayergroupTreeitem(self, item, 1000000 + index)
            for index, child in enumerate(self.children_relation):
                child.ordering = index * 10

    children = property(_get_children, _set_children)

    def __init__(self, name: str='') -> None:
        TreeItem.__init__(self, name=name)


class LayerGroup(TreeGroup):
    __tablename__ = 'layergroup'
    __table_args__ = {'schema': _schema}
    __colanderalchemy_config__ = {
        'title': _('Layers group'),
        'plural': _('Layers groups')
    }
    __mapper_args__ = {'polymorphic_identity': 'group'}
    __c2cgeoform_config__ = {
        'duplicate': True
    }

    id = Column(Integer, ForeignKey(_schema + '.treegroup.id'), primary_key=True, info={
        'colanderalchemy': {
            'missing': colander.drop,
            'widget': HiddenWidget()
        }})
    is_expanded = Column(Boolean, info={
        'colanderalchemy': {
            'title': _('Expanded'),
            'column': 2
        }})  # shouldn't be used in V3
    is_internal_wms = Column(Boolean, info={
        'colanderalchemy': {
            'title': _('Internal WMS'),
            'column': 2
        }})
    # children have radio button instance of check box
    is_base_layer = Column(Boolean, info={
        'colanderalchemy': {
            'title': _('Base layers group'),
            'column': 2
        }})  # Should not be used in V3

    def __init__(
        self, name: str='', is_expanded: bool=False, is_internal_wms: bool=True, is_base_layer: bool=False
    ) -> None:
        TreeGroup.__init__(self, name=name)
        self.is_expanded = is_expanded
        self.is_internal_wms = is_internal_wms
        self.is_base_layer = is_base_layer


# role theme link for restricted theme
restricted_role_theme = Table(
    'restricted_role_theme', Base.metadata,
    Column('role_id', Integer, ForeignKey(_schema + '.role.id'), primary_key=True),
    Column('theme_id', Integer, ForeignKey(_schema + '.theme.id'), primary_key=True),
    schema=_schema
)


class Theme(TreeGroup):
    __tablename__ = 'theme'
    __table_args__ = {'schema': _schema}
    __colanderalchemy_config__ = {
        'title': _('Theme'),
        'plural': _('Themes')
    }
    __mapper_args__ = {'polymorphic_identity': 'theme'}
    __c2cgeoform_config__ = {
        'duplicate': True
    }

    id = Column(Integer, ForeignKey(_schema + '.treegroup.id'), primary_key=True, info={
        'colanderalchemy': {
            'missing': colander.drop,
            'widget': HiddenWidget()
        }})
    ordering = Column(Integer, nullable=False, info={
        'colanderalchemy': {
            'title': _('Order'),
            'widget': HiddenWidget()}})
    public = Column(Boolean, default=True, nullable=False, info={
        'colanderalchemy': {
            'title': _('Public')
        }})
    icon = Column(Unicode, info={
        'colanderalchemy': {'title': _('Icon')}})

    # functionality
    functionalities = relationship(
        'Functionality',
        secondary=theme_functionality,
        cascade='save-update,merge,refresh-expire',
        info={
            'colanderalchemy': {
                'exclude': True,
                'title': _('Functionalities')
            }
        }
    )

    # restricted to role
    restricted_roles = relationship(
        'Role', secondary=restricted_role_theme,
        cascade='save-update,merge,refresh-expire',
        info={
            'colanderalchemy': {
                'exclude': True,
                'title': _('Roles')
            }
        }
    )

    def __init__(self, name: str='', ordering: int=100, icon: str='') -> None:
        TreeGroup.__init__(self, name=name)
        self.ordering = ordering
        self.icon = icon


event.listen(Theme.functionalities, 'set', cache_invalidate_cb)
event.listen(Theme.functionalities, 'append', cache_invalidate_cb)
event.listen(Theme.functionalities, 'remove', cache_invalidate_cb)


class Layer(TreeItem):
    __tablename__ = 'layer'
    __table_args__ = {'schema': _schema}
    __mapper_args__ = {
        'polymorphic_identity': 'layer'  # needed for _identity_class
    }

    id = Column(Integer, ForeignKey(_schema + '.treeitem.id'), primary_key=True)
    public = Column(Boolean, default=True, info={
        'colanderalchemy': {
            'title': _('Public')
        }})
    geo_table = Column(Unicode, info={
        'colanderalchemy': {
            'title': _('Geo table')
        }})
    exclude_properties = Column(Unicode, info={
        'colanderalchemy': {
            'title': _('Exclude properties')
        }})

    def __init__(self, name: str='', public: bool=True) -> None:
        TreeItem.__init__(self, name=name)
        self.public = public


class DimensionLayer(Layer):
    __mapper_args__ = {
        'polymorphic_identity': 'dimensionlayer'  # needed for _identity_class
    }


class LayerV1(Layer):  # Deprecated in v2
    __tablename__ = 'layerv1'
    __table_args__ = {'schema': _schema}
    __colanderalchemy_config__ = {
        'title': _('Layer V1'),
        'plural': _('Layers V1')
    }
    __c2cgeoform_config__ = {
        'duplicate': True
    }
    __mapper_args__ = {'polymorphic_identity': 'layerv1'}

    id = Column(Integer, ForeignKey(_schema + '.layer.id'), primary_key=True, info={
        'colanderalchemy': {
            'missing': None,
            'widget': HiddenWidget()
        }}
    )
    layer = Column(Unicode, info={
        'colanderalchemy': {
            'title': _('Layer name')
        }})
    is_checked = Column(Boolean, default=True, info={
        'colanderalchemy': {
            'title': _('Is checked'),
            'group': 'tree'
        }})  # by default
    icon = Column(Unicode, info={
        'colanderalchemy': {
            'title': _('Icon'),
            'group': 'tree'
        }})  # on the tree
    layer_type = Column(
        Enum(
            'internal WMS',
            'external WMS',
            'WMTS',
            'no 2D',
            native_enum=False),
        info={
            'colanderalchemy': {
                'title': _('Layer type'),
                'widget': SelectWidget(
                    values=(
                        ('', _('- Select -')),
                        ('internal WMS', _('internal WMS')),
                        ('external WMS', _('external WMS')),
                        ('WMTS', _('WMTS')),
                        ('no 2D', _('no 2D'))
                    ))}
        })
    url = Column(Unicode, info={
        'colanderalchemy': {
            'title': _('URL'),
            'group': 'external'
        }})  # for externals
    image_type = Column(
        Enum(
            'image/jpeg',
            'image/png',
            native_enum=False),
        info={
            'colanderalchemy': {
                'title': _('Image type'),
                'widget': SelectWidget(
                    values=(
                        ('', _('- Select -')),
                        ('image/jpeg', 'image/jpeg'),
                        ('image/png', 'image/png')
                    ))}
        })  # for WMS
    style = Column(Unicode, info={
        'colanderalchemy': {
            'title': _('Style')
        }})
    dimensions = Column(Unicode, info={
        'colanderalchemy': {
            'title': _('Dimensions'),
            'group': 'WMTS'
        }})  # for WMTS
    matrix_set = Column(Unicode, info={
        'colanderalchemy': {
            'title': _('Matrix set'),
            'group': 'WMTS'
        }})  # for WMTS
    wms_url = Column(Unicode, info={
        'colanderalchemy': {
            'title': _('WMS URL'),
            'group': 'WMTS'
        }})  # for WMTS
    wms_layers = Column(Unicode, info={
        'colanderalchemy': {
            'title': _('WMS layers'),
            'group': 'WMTS'
        }})  # for WMTS
    query_layers = Column(Unicode, info={
        'colanderalchemy': {
            'title': _('Query layers'),
            'group': 'WMTS'
        }})  # for WMTS
    kml = Column(Unicode, info={
        'colanderalchemy': {
            'title': _('KML'),
            'group': 'other'
        }})  # for kml 3D
    is_single_tile = Column(Boolean, info={
        'colanderalchemy': {
            'title': _('Is single tile'),
            'group': 'external'
        }})  # for extenal WMS
    legend = Column(Boolean, default=True, info={
        'colanderalchemy': {
            'title': _('Legend'),
            'group': 'tree'
        }})  # on the tree
    legend_image = Column(Unicode, info={
        'colanderalchemy': {
            'title': _('Legend image'),
            'group': 'tree'
        }})  # fixed legend image
    legend_rule = Column(Unicode, info={
        'colanderalchemy': {
            'title': _('Legend rule'),
            'group': 'tree'
        }})  # on wms legend only one rule
    is_legend_expanded = Column(Boolean, default=False, info={
        'colanderalchemy': {
            'title': _('Is legend expanded'),
            'group': 'tree'
        }})
    min_resolution = Column(Float, info={
        'colanderalchemy': {
            'title': _('Min resolution'),
            'group': 'other'
        }})  # for all except internal WMS
    max_resolution = Column(Float, info={
        'colanderalchemy': {
            'title': _('Max resolution'),
            'group': 'other'
        }})  # for all except internal WMS
    disclaimer = Column(Unicode, info={
        'colanderalchemy': {
            'title': _('Disclaimer'),
            'group': 'other'
        }})
    # data attribute field in which application can find a human identifiable name or number
    identifier_attribute_field = Column(Unicode, info={
        'colanderalchemy': {
            'title': _('Identifier field'),
            'group': 'other'
        }})
    time_mode = Column(Enum(
        'disabled', 'value', 'range',
        native_enum=False), default='disabled', nullable=False, info={
            'colanderalchemy': {
                'title': _('Time mode'),
                'group': 'other',
                'widget': SelectWidget(values=(
                    ('disabled', _('Disabled')),
                    ('value', _('Value')),
                    ('range', _('Range'))
                ))
            }}
    )
    time_widget = Column(
        Enum('slider', 'datepicker', native_enum=False),
        default='slider',
        nullable=True,
        info={
            'colanderalchemy': {
                'title': _('Time widget'),
                'group': 'other',
                'widget': SelectWidget(values=(
                    ('slider', _('Slider')),
                    ('datepicker', _('Datepicker'))
                ))
            }}
    )

    def __init__(
        self, name: str='', public: bool=True, icon: str='',
        layer_type: str='internal WMS'
    ) -> None:
        Layer.__init__(self, name=name, public=public)
        self.layer = name
        self.icon = icon
        self.layer_type = layer_type


OGCSERVER_TYPE_MAPSERVER = 'mapserver'
OGCSERVER_TYPE_QGISSERVER = 'qgisserver'
OGCSERVER_TYPE_GEOSERVER = 'geoserver'
OGCSERVER_TYPE_OTHER = 'other'

OGCSERVER_AUTH_NOAUTH = 'No auth'
OGCSERVER_AUTH_STANDARD = 'Standard auth'
OGCSERVER_AUTH_GEOSERVER = 'Geoserver auth'
OGCSERVER_AUTH_PROXY = 'Proxy'


class OGCServer(Base):
    __tablename__ = 'ogc_server'
    __table_args__ = {'schema': _schema}
    __colanderalchemy_config__ = {
        'title': _('OGC Server'),
        'plural': _('OGC Servers')
    }
    __c2cgeoform_config__ = {
        'duplicate': True
    }
    id = Column(Integer, primary_key=True, info={
        'colanderalchemy': {
            'widget': HiddenWidget()
        }
    })
    name = Column(Unicode, info={
        'colanderalchemy': {'title': _('Name')}
    })
    description = Column(Unicode, info={
        'colanderalchemy': {'title': _('Description')}
    })
    url = Column(Unicode, nullable=False, info={
        'colanderalchemy': {'title': _('Basic URL')}
    })
    url_wfs = Column(Unicode, info={
        'colanderalchemy': {'title': _('WFS URL')}
    })
    type = Column(
        Enum(
            OGCSERVER_TYPE_MAPSERVER,
            OGCSERVER_TYPE_QGISSERVER,
            OGCSERVER_TYPE_GEOSERVER,
            OGCSERVER_TYPE_OTHER,
            native_enum=False
        ),
        nullable=False,
        info={
            'colanderalchemy': {
                'title': _('Server type'),
                'widget': SelectWidget(
                    values=(
                        (OGCSERVER_TYPE_MAPSERVER, OGCSERVER_TYPE_MAPSERVER),
                        (OGCSERVER_TYPE_QGISSERVER, OGCSERVER_TYPE_QGISSERVER),
                        (OGCSERVER_TYPE_GEOSERVER, OGCSERVER_TYPE_GEOSERVER),
                        (OGCSERVER_TYPE_OTHER, OGCSERVER_TYPE_OTHER)
                    )
                )
            }
        })
    image_type = Column(
        Enum(
            'image/jpeg',
            'image/png',
            native_enum=False
        ),
        nullable=False,
        info={
            'colanderalchemy': {
                'title': _('Image type'),
                'widget': SelectWidget(
                    values=(
                        ('image/jpeg', 'image/jpeg'),
                        ('image/png', 'image/png')
                    )),
                'column': 2}
        })
    auth = Column(
        Enum(
            OGCSERVER_AUTH_NOAUTH,
            OGCSERVER_AUTH_STANDARD,
            OGCSERVER_AUTH_GEOSERVER,
            OGCSERVER_AUTH_PROXY,
            native_enum=False),
        nullable=False,
        info={
            'colanderalchemy': {
                'title': _('Authentication type'),
                'widget': SelectWidget(
                    values=(
                        (OGCSERVER_AUTH_NOAUTH, OGCSERVER_AUTH_NOAUTH),
                        (OGCSERVER_AUTH_STANDARD, OGCSERVER_AUTH_STANDARD),
                        (OGCSERVER_AUTH_GEOSERVER, OGCSERVER_AUTH_GEOSERVER),
                        (OGCSERVER_AUTH_PROXY, OGCSERVER_AUTH_PROXY)
                    )
                ),
                'column': 2
            }
        })
    wfs_support = Column(Boolean, info={
        'colanderalchemy': {'title': _('WFS support'), 'column': 2}
    })
    is_single_tile = Column(Boolean, info={
        'colanderalchemy': {'title': _('Is single tile'), 'column': 2}
    })

    def __init__(
        self, name: str='', description: Optional[str]=None, url: str='https://wms.example.com',
        url_wfs: str=None, type_: str='mapserver', image_type: str='image/png', auth: str='Standard auth',
        wfs_support: bool=True, is_single_tile: bool=False
    ) -> None:
        self.name = name
        self.description = description
        self.url = url
        self.url_wfs = url_wfs
        self.type = type_
        self.image_type = image_type
        self.auth = auth
        self.wfs_support = wfs_support
        self.is_single_tile = is_single_tile

    def __unicode__(self) -> str:
        return self.name or ''  # pragma: no cover


class LayerWMS(DimensionLayer):
    __tablename__ = 'layer_wms'
    __table_args__ = {'schema': _schema}
    __colanderalchemy_config__ = {
        'title': _('WMS Layer'),
        'plural': _('WMS Layers')
    }

    __c2cgeoform_config__ = {
        'duplicate': True
    }

    __mapper_args__ = {'polymorphic_identity': 'l_wms'}

    id = Column(Integer, ForeignKey(_schema + '.layer.id', ondelete='CASCADE'), primary_key=True, info={
        'colanderalchemy': {
            'missing': None,
            'widget': HiddenWidget()
        }})
    ogc_server_id = Column(Integer, ForeignKey(_schema + '.ogc_server.id'), nullable=False, info={
        'colanderalchemy': {
            'title': _('OGC server'),
            'column': 2,
            'widget': deform_ext.RelationSelect2Widget(
                OGCServer,
                'id',
                'name',
                order_by='name',
                default_value=('', _('- Select -')))
        }})
    layer = Column(Unicode, nullable=False, info={
        'colanderalchemy': {
            'title': _('WMS layer name'),
            'column': 2
        }})
    style = Column(Unicode, info={
        'colanderalchemy': {
            'title': _('Style'),
            'column': 2
        }})
    time_mode = Column(Enum(
        'disabled', 'value', 'range',
        native_enum=False), default='disabled', nullable=False, info={
            'colanderalchemy': {
                'title': _('Time mode'),
                'column': 2,
                'widget': SelectWidget(values=(
                    ('disabled', _('Disabled')),
                    ('value', _('Value')),
                    ('range', _('Range'))
                ))
            }}
    )
    time_widget = Column(Enum(
        'slider', 'datepicker',
        native_enum=False), default='slider', nullable=False, info={
            'colanderalchemy': {
                'title': _('Time widget'),
                'column': 2,
                'widget': SelectWidget(values=(
                    ('slider', _('Slider')),
                    ('datepicker', _('Datepicker'))
                ))
            }}
    )

    # relationship with OGCServer
    ogc_server = relationship(
        'OGCServer', info={
            'colanderalchemy': {
                'title': _('OGC server'),
                'exclude': True
            }}
    )

    def __init__(
        self, name: str='', layer: str='', public: bool=True,
        time_mode: str='disabled',
        time_widget: str='slider'
    ) -> None:
        DimensionLayer.__init__(self, name=name, public=public)
        self.layer = layer
        self.time_mode = time_mode
        self.time_widget = time_widget

    @staticmethod
    def get_default(dbsession: Session) -> DimensionLayer:
        return dbsession.query(LayerWMS).filter(LayerWMS.name == 'wms-defaults').one_or_none()


class LayerWMTS(DimensionLayer):
    __tablename__ = 'layer_wmts'
    __table_args__ = {'schema': _schema}
    __colanderalchemy_config__ = {
        'title': _('WMTS Layer'),
        'plural': _('WMTS Layers')
    }
    __c2cgeoform_config__ = {
        'duplicate': True
    }
    __mapper_args__ = {'polymorphic_identity': 'l_wmts'}

    id = Column(Integer, ForeignKey(_schema + '.layer.id'), primary_key=True, info={
        'colanderalchemy': {
            'missing': None,
            'widget': HiddenWidget()
        }})
    url = Column(Unicode, nullable=False, info={
        'colanderalchemy': {
            'title': _('GetCapabilities URL'),
            'column': 2
        }})
    layer = Column(Unicode, nullable=False, info={
        'colanderalchemy': {
            'title': _('WMTS layer name'),
            'column': 2
        }})
    style = Column(Unicode, info={
        'colanderalchemy': {
            'title': _('Style'),
            'column': 2
        }})
    matrix_set = Column(Unicode, info={
        'colanderalchemy': {
            'title': _('Matrix set'),
            'column': 2
        }})
    image_type = Column(
        Enum(
            'image/jpeg',
            'image/png',
            native_enum=False
        ),
        nullable=False,
        info={
            'colanderalchemy': {
                'title': _('Image type'),
                'column': 2,
                'widget': SelectWidget(values=(
                    ('image/jpeg', 'image/jpeg'),
                    ('image/png', 'image/png')))
            }})

    def __init__(self, name: str='', public: bool=True, image_type: str='image/png') -> None:
        DimensionLayer.__init__(self, name=name, public=public)
        self.image_type = image_type

    @staticmethod
    def get_default(dbsession: Session) -> DimensionLayer:
        return dbsession.query(LayerWMTS).filter(LayerWMTS.name == 'wmts-defaults').one_or_none()


# association table role <> restriction area
role_ra = Table(
    'role_restrictionarea', Base.metadata,
    Column('role_id', Integer, ForeignKey(_schema + '.role.id'), primary_key=True),
    Column('restrictionarea_id', Integer, ForeignKey(_schema + '.restrictionarea.id'), primary_key=True),
    schema=_schema
)

# association table layer <> restriction area
layer_ra = Table(
    'layer_restrictionarea', Base.metadata,
    Column('layer_id', Integer, ForeignKey(_schema + '.layer.id'), primary_key=True),
    Column('restrictionarea_id', Integer, ForeignKey(_schema + '.restrictionarea.id'), primary_key=True),
    schema=_schema
)


class RestrictionArea(Base):
    __tablename__ = 'restrictionarea'
    __table_args__ = {'schema': _schema}
    __colanderalchemy_config__ = {
        'title': _('Restriction area'),
        'plural': _('Restriction areas')
    }
    __c2cgeoform_config__ = {
        'duplicate': True
    }
    id = Column(Integer, primary_key=True, info={
        'colanderalchemy': {'widget': HiddenWidget()}}
    )
    area = Column(Geometry('POLYGON', srid=_srid), info={'colanderalchemy': {
        'typ': colander_ext.Geometry('POLYGON', srid=_srid, map_srid=3857)
    }})

    name = Column(Unicode, info={
        'colanderalchemy': {
            'title': _('Name')
        }})
    description = Column(Unicode, info={
        'colanderalchemy': {
            'title': _('Description')
        }})
    readwrite = Column(Boolean, default=False, info={
        'colanderalchemy': {
            'title': _('Read/write')
        }})

    # relationship with Role and Layer
    roles = relationship(
        'Role', secondary=role_ra, info={
            'colanderalchemy': {
                'title': _('Roles'),
                'exclude': True
            }},
        cascade='save-update,merge,refresh-expire',
        backref=backref('restrictionareas', info={
            'colanderalchemy': {
                'exclude': True,
                'title': _('Restriction areas')
            }
        })
    )
    layers = relationship(
        'Layer', secondary=layer_ra, info={
            'colanderalchemy': {
                'title': _('Layers'),
                'exclude': True
            }},
        cascade='save-update,merge,refresh-expire',
        backref=backref('restrictionareas', info={
            'colanderalchemy': {
                'title': _('Restriction areas'),
                'exclude': True
            }}
        )
    )

    def __init__(
            self, name: str='', description: str='', layers: List[Layer]=None, roles: List[Role]=None,
            area: Geometry=None, readwrite: bool=False) -> None:
        if layers is None:
            layers = []
        if roles is None:
            roles = []
        self.name = name
        self.description = description
        self.layers = layers
        self.roles = roles
        self.area = area
        self.readwrite = readwrite

    def __unicode__(self) -> str:  # pragma: no cover
        return self.name or ''


event.listen(RestrictionArea, 'after_insert', cache_invalidate_cb)
event.listen(RestrictionArea, 'after_update', cache_invalidate_cb)
event.listen(RestrictionArea, 'after_delete', cache_invalidate_cb)


# association table interface <> layer
interface_layer = Table(
    'interface_layer', Base.metadata,
    Column('interface_id', Integer, ForeignKey(_schema + '.interface.id'), primary_key=True),
    Column('layer_id', Integer, ForeignKey(_schema + '.layer.id'), primary_key=True),
    schema=_schema
)

# association table interface <> theme
interface_theme = Table(
    'interface_theme', Base.metadata,
    Column('interface_id', Integer, ForeignKey(_schema + '.interface.id'), primary_key=True),
    Column('theme_id', Integer, ForeignKey(_schema + '.theme.id'), primary_key=True),
    schema=_schema
)


class Interface(Base):
    __tablename__ = 'interface'
    __table_args__ = {'schema': _schema}
    __c2cgeoform_config__ = {
        'duplicate': True
    }
    __colanderalchemy_config__ = {
        'title': _('Interface'),
        'plural': _('Interfaces')
    }

    id = Column(Integer, primary_key=True, info={
        'colanderalchemy': {
            'widget': HiddenWidget()
        }})
    name = Column(Unicode, info={
        'colanderalchemy': {'title': _('Name')}})
    description = Column(Unicode, info={
        'colanderalchemy': {'title': _('Description')}})

    # relationship with Layer and Theme
    layers = relationship(
        'Layer', secondary=interface_layer,
        cascade='save-update,merge,refresh-expire',
        info={
            'colanderalchemy': {
                'title': _('Layers'),
                'exclude': True
            },
            'c2cgeoform': {
                'duplicate': False
            }},
        backref=backref('interfaces', info={
            'colanderalchemy': {
                'title': _('Interfaces'),
                'exclude': True
            }}
        )
    )
    theme = relationship(
        'Theme',
        secondary=interface_theme,
        cascade='save-update,merge,refresh-expire',
        info={
            'colanderalchemy': {
                'title': _('Themes'),
                'exclude': True
            },
            'c2cgeoform': {
                'duplicate': False
            }},
        backref=backref('interfaces', info={
            'colanderalchemy': {
                'title': _('Interfaces'),
                'exclude': True
            }}
        )
    )

    def __init__(self, name: str='', description: str='') -> None:
        self.name = name
        self.description = description

    def __unicode__(self) -> str:  # pragma: no cover
        return self.name or ''


class Metadata(Base):
    __tablename__ = 'metadata'
    __table_args__ = {'schema': _schema}

    id = Column(Integer, primary_key=True, info={'colanderalchemy': {'widget': HiddenWidget()}})
    name = Column(Unicode, info={
        'colanderalchemy': {
            'title': _('Name'),
        }
    })
    value = Column(Unicode, info={
        'colanderalchemy': {
            'exclude': True
        }
    })
    description = Column(Unicode, info={
        'colanderalchemy': {
            'title': _('Description'),
            'widget': TextAreaWidget()
        }
    })

    item_id = Column('item_id',
                     Integer,
                     ForeignKey(_schema + '.treeitem.id'),
                     nullable=False,
                     info={
                         'colanderalchemy': {
                             'exclude': True},
                         'c2cgeoform': {
                             'duplicate': False}})
    item = relationship(
        'TreeItem',
        info={'c2cgeoform': {'duplicate': False},
              'colanderalchemy': {'exclude': True}
              },
        backref=backref(
            'metadatas',
            cascade='save-update,merge,delete,delete-orphan,expunge',
            order_by='Metadata.name',
            info={
                'colanderalchemy': {
                    'title': _('Metadatas'),
                    'exclude': True
                }
            }
        )
    )

    def __init__(self, name: str='', value: str='') -> None:
        self.name = name
        self.value = value

    def __unicode__(self) -> str:  # pragma: no cover
        return '{0!s}: {1!s}'.format(self.name or '', self.value or '')


event.listen(Metadata, 'after_insert', cache_invalidate_cb, propagate=True)
event.listen(Metadata, 'after_update', cache_invalidate_cb, propagate=True)
event.listen(Metadata, 'after_delete', cache_invalidate_cb, propagate=True)


class Dimension(Base):
    __tablename__ = 'dimension'
    __table_args__ = {'schema': _schema}

    id = Column(Integer, primary_key=True, info={'colanderalchemy': {'widget': HiddenWidget()}})
    name = Column(Unicode, info={
        'colanderalchemy': {
            'title': _('Name')
        }
    })
    value = Column(Unicode, info={
        'colanderalchemy': {
            'title': _('Value')
        }
    })
    description = Column(Unicode, info={
        'colanderalchemy': {
            'title': _('Description'),
            'widget': TextAreaWidget()
        }
    })

    layer_id = Column('layer_id',
                      Integer,
                      ForeignKey(_schema + '.layer.id'),
                      nullable=False,
                      info={
                          'colanderalchemy': {
                              'exclude': True
                          },
                          'c2cgeoform': {
                              'duplicate': False
                          }})
    layer = relationship(
        'DimensionLayer',
        info={'c2cgeoform': {'duplicate': False},
              'colanderalchemy': {'exclude': True}
              },
        backref=backref(
            'dimensions',
            cascade='save-update,merge,delete,delete-orphan,expunge',
            info={
                'colanderalchemy': {
                    'title': _('Dimensions'),
                    'exclude': True
                }
            }
        )
    )

    def __init__(self, name: str='', value: str='', layer: str=None) -> None:
        self.name = name
        self.value = value
        if layer is not None:
            self.layer = layer

    def __unicode__(self) -> str:  # pragma: no cover
        return self.name or ''
