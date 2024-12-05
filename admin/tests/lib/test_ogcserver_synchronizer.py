import re
from unittest.mock import patch

import pytest
from lxml import etree
from owslib.wms import WebMapService
from pyramid import testing

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
    return f"""
<WMS_Capabilities>
<Service>
  <Name>OGC:WMS</Name>
</Service>
<Capability>
  {content}
</Capability>
</WMS_Capabilities>
"""


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
    def synchronizer(self, request, server=None, force_parents=False, force_ordering=False, clean=False):
        from c2cgeoportal_admin.lib.ogcserver_synchronizer import OGCServerSynchronizer

        return OGCServerSynchronizer(
            request=request,
            ogc_server=server or ogc_server(),
            force_parents=force_parents,
            force_ordering=force_ordering,
            clean=clean,
        )

    def test_wms_service_mapserver(self, web_request):
        synchronizer = self.synchronizer(web_request)

        wms_capabilities = synchronizer.wms_capabilities()

        wms_service = WebMapService(None, xml=wms_capabilities)
        assert wms_service.identification.type == "OGC:WMS"

        url = re.escape(
            "http://mapserver:8080/?SERVICE=WMS&VERSION=1.1.1&REQUEST=GetCapabilities&ROLE_IDS=0&USER_ID=0"
        )
        assert re.match(
            rf"Get WMS GetCapabilities from: {url}\nGot response 200 in \d+.\d+s.\n",
            synchronizer.report(),
        ), synchronizer.report()

    @patch(
        "c2cgeoportal_admin.lib.ogcserver_synchronizer.OGCServerSynchronizer.wms_capabilities",
        return_value=wms_capabilities(),
    )
    def test_check_layers(self, cap_mock, web_request, dbsession):
        from c2cgeoportal_commons.models import main

        server = ogc_server()
        dbsession.add(server)

        layer1 = main.LayerWMS(name="layer1", layer="layer1")
        layer1.ogc_server = server
        dbsession.add(layer1)

        layer_missing = main.LayerWMS(name="layer_missing", layer="layer_missing")
        layer_missing.ogc_server = server
        dbsession.add(layer_missing)

        style_missing = main.LayerWMS(name="style_missing", layer="layer1")
        style_missing.ogc_server = server
        style_missing.style = "style_missing"
        dbsession.add(style_missing)

        dbsession.flush()

        layers = dbsession.query(main.LayerWMS).filter(main.LayerWMS.ogc_server == server)
        assert layers.count() == 3

        synchronizer = self.synchronizer(web_request, server)
        synchronizer.check_layers()
        assert synchronizer.report() == (
            "Layer layer_missing does not exists on OGC server\n"
            "Style style_missing does not exists in Layer layer1\n"
            "Checked 3 layers, 2 are invalid\n"
        )

    def test_synchronize_mapserver(self, web_request):
        synchronizer = self.synchronizer(web_request)
        synchronizer.synchronize()

    @patch(
        "c2cgeoportal_admin.lib.ogcserver_synchronizer.OGCServerSynchronizer.wms_capabilities",
        return_value=wms_capabilities(),
    )
    def test_synchronize_dry_run(self, cap_mock, web_request, dbsession):
        from c2cgeoportal_commons.models import main

        assert dbsession.query(main.TreeItem).count() == 0

        synchronizer = self.synchronizer(web_request)
        synchronizer.synchronize(dry_run=True)

        assert dbsession.query(main.TreeItem).count() == 0

        assert synchronizer.report() == (
            "Layer theme1 added as new theme\n"
            "Layer group1 added as new group in theme theme1\n"
            "Layer layer1 added as new layer in group group1\n"
            "Layer layer_in_theme added as new layer with no parent\n"
            "Layer layer_with_no_parent added as new layer with no parent\n"
            "0 items found\n"
            "1 themes added\n"
            "1 groups added\n"
            "0 groups removed\n"
            "3 layers added\n"
            "0 layers removed\n"
            "Rolling back transaction due to dry run\n"
        )

    @patch(
        "c2cgeoportal_admin.lib.ogcserver_synchronizer.OGCServerSynchronizer.wms_capabilities",
        return_value=wms_capabilities(),
    )
    def test_synchronize_success(self, cap_mock, web_request, dbsession):
        from c2cgeoportal_commons.models import main

        interface = main.Interface(name="desktop")
        dbsession.add(interface)

        synchronizer = self.synchronizer(web_request)
        synchronizer.synchronize()

        theme1 = dbsession.query(main.Theme).one()
        assert theme1.name == "theme1"
        assert len(theme1.interfaces) == 1

        group1 = dbsession.query(main.LayerGroup).one()
        assert group1.name == "group1"
        assert group1.parents == [theme1]

        layer1 = dbsession.query(main.LayerWMS).filter(main.LayerWMS.name == "layer1").one()
        assert layer1.name == "layer1"
        assert layer1.parents == [group1]
        assert len(layer1.interfaces) == 1

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
            "0 items found\n"
            "1 themes added\n"
            "1 groups added\n"
            "0 groups removed\n"
            "3 layers added\n"
            "0 layers removed\n"
        )

    @patch(
        "c2cgeoportal_admin.lib.ogcserver_synchronizer.OGCServerSynchronizer.wms_capabilities",
        return_value=wms_capabilities(),
    )
    def test_synchronize_force_parents(self, cap_mock, web_request, dbsession):
        from c2cgeoportal_commons.models import main

        interface = main.Interface(name="desktop")
        dbsession.add(interface)

        server = ogc_server()
        dbsession.add(server)

        dbsession.flush()

        # Run first synchronization
        synchronizer = self.synchronizer(web_request, server)
        synchronizer.synchronize()

        # Change some parents
        theme2 = main.Theme(name="theme2")
        dbsession.add(theme2)
        group1 = dbsession.query(main.LayerGroup).one()
        group1.parents_relation = [main.LayergroupTreeitem(group=theme2)]

        group2 = main.LayerGroup(name="group2")
        dbsession.add(theme2)
        layer1 = dbsession.query(main.LayerWMS).filter(main.LayerWMS.name == "layer1").one()
        layer1.parents_relation = [main.LayergroupTreeitem(group=group2)]

        dbsession.flush()

        # Run new synchronization with force_parents
        synchronizer = self.synchronizer(web_request, server, force_parents=True)
        synchronizer.synchronize()

        theme1 = dbsession.query(main.Theme).filter(main.Theme.name == "theme1").one()
        assert group1.parents == [theme1]
        assert layer1.parents == [group1]

        layer_in_theme = dbsession.query(main.LayerWMS).filter(main.LayerWMS.name == "layer_in_theme").one()
        assert layer_in_theme.parents == []

        layer_with_no_parent = (
            dbsession.query(main.LayerWMS).filter(main.LayerWMS.name == "layer_with_no_parent").one()
        )
        assert layer_with_no_parent.parents == []

        assert synchronizer.report() == (
            "Group group1 moved to theme1\n"
            "Layer layer1 moved to group1\n"
            "5 items found\n"
            "0 themes added\n"
            "0 groups added\n"
            "0 groups removed\n"
            "0 layers added\n"
            "0 layers removed\n"
        )

    @patch(
        "c2cgeoportal_admin.lib.ogcserver_synchronizer.OGCServerSynchronizer.wms_capabilities",
        return_value=wms_capabilities(),
    )
    def test_synchronize_force_ordering(self, cap_mock, web_request, dbsession):
        from c2cgeoportal_commons.models import main

        interface = main.Interface(name="desktop")
        dbsession.add(interface)

        server = ogc_server()

        # Run first synchronization
        with patch(
            "c2cgeoportal_admin.lib.ogcserver_synchronizer.OGCServerSynchronizer.wms_capabilities",
            return_value=wms_capabilities(
                """
                <Layer>
                    <Name>root</Name>
                    <Layer>
                        <Name>theme1</Name>
                        <Layer>
                            <Name>theme1_group1</Name>
                            <Layer>
                                <Name>theme1_group1_layer1</Name>
                            </Layer>
                            <Layer>
                                <Name>theme1_group1_layer2</Name>
                            </Layer>
                        </Layer>
                        <Layer>
                            <Name>theme1_group2</Name>
                            <Layer>
                                <Name>theme1_group2_layer1</Name>
                            </Layer>
                        </Layer>
                    </Layer>
                    <Layer>
                        <Name>theme2</Name>
                        <Layer>
                            <Name>theme2_group1</Name>
                            <Layer>
                                <Name>theme2_group1_layer1</Name>
                            </Layer>
                        </Layer>
                    </Layer>
                </Layer>
                """
            ),
        ):
            synchronizer = self.synchronizer(web_request, server)
            synchronizer.synchronize()

        # Run second synchronization with force_order=True
        with patch(
            "c2cgeoportal_admin.lib.ogcserver_synchronizer.OGCServerSynchronizer.wms_capabilities",
            return_value=wms_capabilities(
                """
                <Layer>
                    <Name>root</Name>
                    <Layer>
                        <Name>theme2</Name>
                        <Layer>
                            <Name>theme2_group1</Name>
                            <Layer>
                                <Name>theme2_group1_layer1</Name>
                            </Layer>
                        </Layer>
                    </Layer>
                    <Layer>
                        <Name>theme1</Name>
                        <Layer>
                            <Name>theme1_group2</Name>
                            <Layer>
                                <Name>theme1_group2_layer1</Name>
                            </Layer>
                        </Layer>
                        <Layer>
                            <Name>theme1_group1</Name>
                            <Layer>
                                <Name>theme1_group1_layer2</Name>
                            </Layer>
                            <Layer>
                                <Name>theme1_group1_layer1</Name>
                            </Layer>
                        </Layer>
                    </Layer>
                </Layer>
                """
            ),
        ):
            synchronizer = self.synchronizer(
                web_request, server, force_parents=True, force_ordering=True, clean=True
            )
            synchronizer.synchronize()

        theme1 = dbsession.query(main.Theme).filter(main.Theme.name == "theme1").one()
        # theme2 = dbsession.query(main.Theme).filter(main.Theme.name == "theme2").one()
        # assert theme1.ordering > theme2.ordering
        # Difficult to do as layer tree can contain themes from multiple OGCServer

        groups = theme1._get_children()
        assert groups[0].name == "theme1_group2"
        assert groups[1].name == "theme1_group1"

        layers = groups[1]._get_children()
        assert layers[0].name == "theme1_group1_layer2"
        assert layers[1].name == "theme1_group1_layer1"

        assert synchronizer.report() == (
            "Children of theme1_group1 have been sorted\n"
            "Children of theme1 have been sorted\n"
            "Checked 4 layers, 0 are invalid\n"
            "9 items found\n"
            "0 themes added\n"
            "0 groups added\n"
            "0 groups removed\n"
            "0 layers added\n"
            "0 layers removed\n"
        )

    @patch(
        "c2cgeoportal_admin.lib.ogcserver_synchronizer.OGCServerSynchronizer.wms_capabilities",
        return_value=wms_capabilities(),
    )
    def test_synchronize_clean(self, cap_mock, web_request, dbsession):
        from c2cgeoportal_commons.models import main

        server = ogc_server()
        dbsession.add(server)

        layer1 = main.LayerWMS(name="layer1", layer="layer1")
        layer1.ogc_server = server
        dbsession.add(layer1)

        layer_missing = main.LayerWMS(name="layer_missing", layer="layer_missing")
        layer_missing.ogc_server = server
        dbsession.add(layer_missing)

        empty_group = main.LayerGroup(name="empty_group")
        dbsession.add(empty_group)

        dbsession.flush()

        synchronizer = self.synchronizer(web_request, server, clean=True)
        synchronizer.synchronize()

        assert dbsession.query(main.LayerWMS).filter(main.LayerWMS.name == "layer_missing").count() == 0
        assert dbsession.query(main.LayerGroup).filter(main.LayerGroup.name == "empty_group").count() == 0

        assert synchronizer.report() == (
            "Layer theme1 added as new theme\n"
            "Layer group1 added as new group in theme theme1\n"
            "Layer layer_in_theme added as new layer with no parent\n"
            "Layer layer_with_no_parent added as new layer with no parent\n"
            "Layer layer_missing does not exists on OGC server\n"
            "Removed layer layer_missing\n"
            "Removed empty group empty_group\n"
            "Removed empty group group1\n"
            "Checked 4 layers, 1 are invalid\n"
            "1 items found\n"
            "1 themes added\n"
            "1 groups added\n"
            "2 groups removed\n"
            "2 layers added\n"
            "1 layers removed\n"
        )

    def test_get_layer_wms_defaut(self, web_request, dbsession):
        """We should copy properties from default LayerWMS."""
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
            layer = synchronizer.get_layer_wms(el, None)

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

    def test_get_layer_wms_defaut_style_not_exists(self, web_request, dbsession):
        """We should not copy style from default LayerWMS if does not exist in capabilities."""
        from c2cgeoportal_commons.models import main

        synchronizer = self.synchronizer(web_request)

        default_wms = main.LayerWMS()
        default_wms.style = "not_existing_style"
        synchronizer._default_wms = default_wms

        synchronizer._interfaces = []

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

        layer = synchronizer.get_layer_wms(el, None)
        assert layer.style is None
