from contextlib import contextmanager
import sys
try:
    from xml.etree.cElementTree import ElementTree, TreeBuilder
except ImportError:
    from xml.etree.ElementTree import ElementTree, TreeBuilder

import geoalchemy
import sqlalchemy


@contextmanager
def tag(tb, name, attrs={}):
    tb.start(name, attrs)
    yield tb
    tb.end(name)


def pretty_write(io, element, indent='\t', prefix=''):
    """Writes element to io with indentation."""
    attrs = ''.join(' %s="%s"' % item for item in element.items())
    children = element.getchildren()
    if children:
        io.write('%s<%s%s>\n' % (prefix, element.tag, attrs))
        for child in children:
            pretty_write(io, child, indent, prefix + indent)
        io.write('%s</%s>\n' % (prefix, element.tag))
    elif element.text:
        io.write('%s<%s%s>%s</%s>\n' % (prefix, element.tag, attrs, element.text, element.tag))
    else:
        io.write('%s<%s%s/>\n' % (prefix, element.tag, attrs))


SIMPLE_XSD_TYPES = {
        # GeoAlchemy types
        geoalchemy.Curve:              'gml:CurvePropertyType',
        geoalchemy.GeometryCollection: 'gml:GeometryCollectionPropertyType',
        geoalchemy.LineString:         'gml:LineStringPropertyType',
        geoalchemy.MultiLineString:    'gml:MultiLineStringPropertyType',
        geoalchemy.MultiPoint:         'gml:MultiPointPropertyType',
        geoalchemy.MultiPolygon:       'gml:MultiPolygonPropertyType',
        geoalchemy.Point:              'gml:PointPropertyType',
        geoalchemy.Polygon:            'gml:PolygonPropertyType',
        # SQLAlchemy types
        sqlalchemy.BigInteger:   'xsd:integer',
        sqlalchemy.Boolean:      'xsd:boolean',
        sqlalchemy.Date:         'xsd:date',
        sqlalchemy.DateTime:     'xsd:dateTime',
        sqlalchemy.Float:        'xsd:double',
        sqlalchemy.Integer:      'xsd:integer',
        sqlalchemy.Interval:     'xsd:duration',
        sqlalchemy.LargeBinary:  'xsd:base64Binary',
        sqlalchemy.PickleType:   'xsd:base64Binary',
        sqlalchemy.SmallInteger: 'xsd:integer',
        sqlalchemy.Time:         'xsd:time',
        }


def add_column_xsd(tb, column):
    """Add the XSD for a single column to tb (a TreeBuilder)."""
    attrs = {}
    attrs['name'] = column.name
    if column.nullable:
        attrs['minOccurs'] = str(0)
        attrs['nillable'] = 'true'
    if column.foreign_keys:
        if len(column.foreign_keys) != 1:
            raise RuntimeError('Column %s has more than one foreign key' % (column.name,))
        foreign_key = next(iter(column.foreign_keys))
        attrs['type'] = foreign_key._colspec.split('.', 2)[0]
        with tag(tb, 'xsd:element', attrs) as tb:
            return tb
    for cls, xsd_type in SIMPLE_XSD_TYPES.iteritems():
        if isinstance(column.type, cls):
            attrs['type'] = xsd_type
            with tag(tb, 'xsd:element', attrs) as tb:
                return tb
    if isinstance(column.type, sqlalchemy.Enum):
        with tag(tb, 'xsd:element', attrs) as tb:
            with tag(tb, 'xsd:simpleType') as tb:
                with tag(tb, 'xsd:restriction', {'base': 'xsd:string'}) as tb:
                    for enum in column.type.enums:
                        with tag(tb, 'xsd:enumeration', {'value': enum}):
                            pass
                    return tb
    if isinstance(column.type, sqlalchemy.Numeric):
        if column.type.scale is None and column.type.precision is None:
            attrs['type'] = 'xsd:decimal'
            with tag(tb, 'xsd:element', attrs) as tb:
                return tb
        else:
            with tag(tb, 'xsd:element', attrs) as tb:
                with tag(tb, 'xsd:simpleType') as tb:
                    with tag(tb, 'xsd:restriction', {'base': 'xsd:decimal'}) as tb:
                        if column.type.scale is not None:
                            with tag(tb, 'xsd:fractionDigits', {'value': str(column.type.scale)}) as tb:
                                pass
                        if column.type.precision is not None:
                            with tag(tb, 'xsd:totalDigits', {'value': str(column.type.precision)}) as tb:
                                pass
                        return tb
    if isinstance(column.type, sqlalchemy.String) \
        or isinstance(column.type, sqlalchemy.Text) \
        or isinstance(column.type, sqlalchemy.Unicode) \
        or isinstance(column.type, sqlalchemy.UnicodeText):
        if column.type.length is None:
            attrs['type'] = 'xsd:string'
            with tag(tb, 'xsd:element', attrs) as tb:
                return tb
        else:
            with tag(tb, 'xsd:element', attrs) as tb:
                with tag(tb, 'xsd:simpleType') as tb:
                    with tag(tb, 'xsd:restriction', {'base': 'xsd:string'}) as tb:
                        with tag(tb, 'xsd:maxLength', {'value': str(column.type.length)}):
                            return tb
    raise RuntimeError('Unsupported column type %r' % (column.type.__class__,))


def add_table_xsd(tb, table):
    """Add the XSD for a single table to tb (a TreeBuilder)."""
    with tag(tb, 'xsd:complexType', {'name': table.name}) as tb:
        with tag(tb, 'xsd:complexContent') as tb:
            with tag(tb, 'xsd:extension', {'base': 'gml:AbstractFeatureType'}) as tb:
                with tag(tb, 'xsd:sequence') as tb:
                    for column in table.columns:
                        add_column_xsd(tb, column)
                    return tb


def add_metadata_xsd(tb, metadata):
    """Add the XSD for all tables in metadata to tb (a TreeBuilder)."""
    for name, table in metadata.tables.iteritems():
        add_table_xsd(tb, table)
    return tb


def get_xsd_helper(io, obj, create_func, pretty=False):
    """A helper function to factor out the generation of the XML boilerplate."""
    attrs = {}
    attrs['xmlns:gml'] = 'http://www.opengis.net/gml'
    attrs['xmlns:xsd'] = 'http://www.w3.org/2001/XMLSchema'
    tb = TreeBuilder()
    with tag(tb, 'xsd:schema', attrs) as tb:
        create_func(tb, obj)
    element = tb.close()
    if pretty:
        io.write('<?xml version="1.0" encoding="utf-8"?>\n')
        pretty_write(io, element)
    else:
        ElementTree(element).write(io, encoding='utf-8')
    return io


def get_table_xsd(io, table, pretty=False):
    """Write the XSD for table to io and return io."""
    return get_xsd_helper(io, table, add_table_xsd, pretty=pretty)


def get_metadata_xsd(io, metadata, pretty=False):
    """Write the XSD for all the tables in metadata to io and return io."""
    return get_xsd_helper(io, metadata, add_metadata_xsd, pretty=pretty)
