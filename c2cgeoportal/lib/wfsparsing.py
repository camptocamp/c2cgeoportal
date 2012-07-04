from io import StringIO, BytesIO

from xml.sax import make_parser, handler
from xml.sax.saxutils import XMLFilterBase, XMLGenerator
from xml.sax.xmlreader import InputSource


class _XMLFilterGetFeature(handler.ContentHandler):
    """
    An XMLFilterBase subclass to determine if the XML doc
    corresponds to a WFS GetFeature request.
    """
    def __init__(self):
        self.result = False

    def startElement(self, name, attrs):
        if name == "wfs:GetFeature":
            self.result = True


class _XMLFilterLimit(XMLFilterBase):
    """
    An XMLFilterBase subclass to limit the number of features
    from a WFS FeatureCollection document.
    """
    def __init__(self, upstream, downstream, limit=200):
        XMLFilterBase.__init__(self, upstream)
        self._count = 0
        self._limit = limit
        self._downstream = downstream

    def startDocument(self):
        # Set the initial state, and set up the stack of states
        self._exportContent = True

    def startElement(self, name, attrs):
        if name == "gml:featureMember":
            if self._count >= self._limit:
                self._exportContent = False
            else:
                self._count += 1
        # Only forward the event if the state warrants it
        if self._exportContent:
            self._downstream.startElement(name, attrs)

    def endElement(self, name):
        # Only forward the event if the state warrants it
        if self._exportContent:
            self._downstream.endElement(name)

        if name == "gml:featureMember":
            self._exportContent = True

    def characters(self, content):
        # Only forward the event if the state warrants it
        if self._exportContent:
            self._downstream.characters(content)


class _StringIO(StringIO):
    """
    A specific io.StringIO implementation that converts the
    string object to a unicode object before writing into
    the stream.
    """
    def write(self, s):
        return StringIO.write(self, unicode(s, 'utf-8'))


def is_get_feature(content):
    """
    Determine if the XML string is a WFS GetFeature
    request.
    """

    parser = make_parser()
    _filter = _XMLFilterGetFeature()
    parser.setContentHandler(_filter)
    input_source = InputSource()

    if isinstance(content, str):
        content = unicode(content, 'utf-8')
    _input = BytesIO(content.encode('utf-8'))

    input_source.setByteStream(_input)
    parser.parse(input_source)
    _input.close()
    return _filter.result


def limit_featurecollection(content, limit=200):
    """
    Parse a WFS FeatureCollection XML string and produce a
    similar string with at most 200 features.
    """

    parser = make_parser()

    if isinstance(content, str):
        content = unicode(content, 'utf-8')

    _input = BytesIO(content.encode('utf-8'))

    input_source = InputSource()
    input_source.setByteStream(_input)

    output = _StringIO()
    downstream = XMLGenerator(output, 'utf-8')

    _filter = _XMLFilterLimit(parser, downstream, limit=limit)
    _filter.parse(input_source)

    result = output.getvalue()

    _input.close()
    output.close()

    return result
