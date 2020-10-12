import re
from unittest.mock import patch

from lxml import etree
from owslib.wms import WebMapService
from pyramid import testing
import pytest


DEFAULT_CONTENT = """
<Layer>
    <Name>root</Name>
    <Layer>
        <Name>theme1</Name>
        <Layer>
            <Name>group1</Name>
            <Layer>
                <Name>layer1</Name>
            </Layer>
        </Layer>
        <Layer>
            <Name>layer_in_theme</Name>
        </Layer>
    </Layer>
    <Layer>
        <Name>layer_with_no_parent</Name>
    </Layer>
</Layer>
"""


def wms_capabilities(content=DEFAULT_CONTENT):
    return """
<WMS_Capabilities>
<Service>
  <Name>OGC:WMS</Name>
</Service>
<Capability>
  {}
</Capability>
</WMS_Capabilities>
""".format(
        content
    )


@pytest.fixture(scope="function")
def web_request(dbsession):
    request = testing.DummyRequest()
    request.dbsession = dbsession
    yield request


def ogc_server(**kwargs):
    from c2cgeoportal_commons.models import main

    return main.OGCServer(
        **{
            **{
                "name": "Test server",
                "description": "Test server",
                "url": "config://mapserver",
                "image_type": "image/png",
                "auth": main.OGCSERVER_AUTH_NOAUTH,
            },
            **kwargs,
        }
    )


@pytest.mark.usefixtures("test_app", "transact")
class TestOGCServerSynchronizer:
    def synchronizer(self, request):
        from c2cgeoportal_admin.lib.ogcserver_synchronizer import OGCServerSynchronizer

        return OGCServerSynchronizer(request=request, ogc_server=ogc_server())

    def test_wms_service_mapserver(self, web_request):
        synchronizer = self.synchronizer(web_request)

        wms_capabilities = synchronizer.wms_capabilities()

        wms_service = WebMapService(None, xml=wms_capabilities)
        assert wms_service.identification.type == "OGC:WMS"

        url = re.escape(
            "http://mapserver:8080/?SERVICE=WMS&VERSION=1.1.1&REQUEST=GetCapabilities&ROLE_ID=0&USER_ID=0"
        )
        assert re.match(
            r"Get WMS GetCapabilities from: {url}\nGot response 200 in \d+.\d+s.\n".format(url=url),
            synchronizer.report(),
        )

    def test_synchronize_mapserver(self, web_request):
        synchronizer = self.synchronizer(web_request)
        synchronizer.synchronize()

    @patch(
        "c2cgeoportal_admin.lib.ogcserver_synchronizer.OGCServerSynchronizer.wms_capabilities",
        return_value=wms_capabilities(),
    )
    def test_synchronize_success(self, cap_mock, web_request, dbsession):
        from c2cgeoportal_commons.models import main

        assert dbsession.query(main.TreeItem).count() == 0

        synchronizer = self.synchronizer(web_request)
        synchronizer.synchronize()

        theme1 = dbsession.query(main.Theme).one()
        assert theme1.name == "theme1"

        group1 = dbsession.query(main.LayerGroup).one()
        assert group1.name == "group1"
        assert group1.parents == [theme1]

        layer1 = dbsession.query(main.LayerWMS).filter(main.LayerWMS.name == "layer1").one()
        assert layer1.name == "layer1"
        assert layer1.parents == [group1]

        layer_in_theme = dbsession.query(main.LayerWMS).filter(main.LayerWMS.name == "layer_in_theme").one()
        assert layer_in_theme.name == "layer_in_theme"
        assert layer_in_theme.parents == []

        layer_with_no_parent = (
            dbsession.query(main.LayerWMS).filter(main.LayerWMS.name == "layer_with_no_parent").one()
        )
        assert layer_with_no_parent.name == "layer_with_no_parent"
        assert layer_with_no_parent.parents == []

        assert synchronizer.report() == (
            "Layer theme1 added as new theme\n"
            "Layer group1 added as new group in theme theme1\n"
            "Layer layer1 added as new layer in group group1\n"
            "Layer layer_in_theme added as new layer with no parent\n"
            "Layer layer_with_no_parent added as new layer with no parent\n"
            "0 items were found\n"
            "1 themes were added\n"
            "1 groups were added\n"
            "3 layers were added\n"
        )

    def test_create_layer_wms_defaut(self, web_request, dbsession):
        """We should copy properties from default LayerWMS"""
        from c2cgeoportal_commons.models import main

        synchronizer = self.synchronizer(web_request)

        default_wms = main.LayerWMS()
        default_wms.description = "Default description"
        default_wms.metadatas = [main.Metadata(name="isExpanded", value="True")]
        default_wms.exclude_properties = "excluded_property"
        default_wms.interfaces = [main.Interface("interface")]
        default_wms.dimensions = [
            main.Dimension(name="dim", value=None, field="dim", description="description")
        ]
        default_wms.style = "default_style"

        el = etree.fromstring(
            """
<Layer>
    <Name>layer1</Name>
    <Style>
        <Name>default_style</Name>
        <Title>default_style</Title>
    </Style>
</Layer>
"""
        )

        with patch.object(synchronizer, "_default_wms", default_wms):
            layer = synchronizer.create_layer_wms(el)

            assert layer.description == "Default description"
            assert len(layer.metadatas) == 1
            assert layer.metadatas[0].name == "isExpanded"
            assert layer.metadatas[0].value == "True"
            assert layer.exclude_properties == "excluded_property"
            assert len(layer.interfaces) == 1
            assert layer.interfaces[0].name == "interface"
            assert len(layer.dimensions) == 1
            assert layer.dimensions[0].name == "dim"
            assert layer.dimensions[0].value is None
            assert layer.dimensions[0].field == "dim"
            assert layer.dimensions[0].description == "description"
            assert layer.style == "default_style"

    def test_create_layer_wms_defaut_style_not_exists(self, web_request, dbsession):
        """We should not copy style from default LayerWMS if does not exist in capabilities"""
        from c2cgeoportal_commons.models import main

        synchronizer = self.synchronizer(web_request)

        default_wms = main.LayerWMS()
        default_wms.style = "not_existing_style"

        el = etree.fromstring(
            """
<Layer>
    <Name>layer1</Name>
    <Style>
        <Name>default</Name>
        <Title>default</Title>
    </Style>
</Layer>
"""
        )

        with patch.object(synchronizer, "_default_wms", default_wms):
            layer = synchronizer.create_layer_wms(el)
            assert layer.style is None
