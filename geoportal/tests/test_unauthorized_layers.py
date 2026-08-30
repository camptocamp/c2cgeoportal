# Copyright (c) 2026, Camptocamp SA
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
# (INCLUDING, BUT OR LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# The views and conclusions contained in the software and documentation are those
# of the authors and should not be interpreted as representing official policies,
# either expressed or implied, of the FreeBSD Project.


from unittest import TestCase
from unittest.mock import MagicMock, patch


class TestUnauthorizedLayers(TestCase):
    """Tests for get_unauthorized_layers."""

    @patch("c2cgeoportal_geoportal.lib.layers.get_protected_layers")
    @patch("c2cgeoportal_geoportal.lib.layers.get_private_layers")
    def test_no_private_layers(self, mock_private, mock_protected):
        """When there are no private layers, nothing is unauthorized."""
        from c2cgeoportal_geoportal.lib.layers import get_unauthorized_layers

        mock_private.return_value = {}
        mock_protected.return_value = {}
        request = MagicMock()

        result = get_unauthorized_layers(request, 1, {})
        self.assertEqual(result, set())

    @patch("c2cgeoportal_geoportal.lib.layers.get_protected_layers")
    @patch("c2cgeoportal_geoportal.lib.layers.get_private_layers")
    def test_private_layer_not_protected(self, mock_private, mock_protected):
        """A private layer the user cannot access is unauthorized."""
        from c2cgeoportal_geoportal.lib.layers import get_unauthorized_layers

        layer = MagicMock()
        layer.layer = "private_layer"
        mock_private.return_value = {1: layer}
        mock_protected.return_value = {}
        request = MagicMock()

        result = get_unauthorized_layers(request, 1, {})
        self.assertEqual(result, {"private_layer"})

    @patch("c2cgeoportal_geoportal.lib.layers.get_protected_layers")
    @patch("c2cgeoportal_geoportal.lib.layers.get_private_layers")
    def test_private_layer_protected(self, mock_private, mock_protected):
        """A private layer the user can access is not unauthorized."""
        from c2cgeoportal_geoportal.lib.layers import get_unauthorized_layers

        layer = MagicMock()
        layer.layer = "private_layer"
        mock_private.return_value = {1: layer}
        mock_protected.return_value = {1: layer}
        request = MagicMock()

        result = get_unauthorized_layers(request, 1, {})
        self.assertEqual(result, set())

    @patch("c2cgeoportal_geoportal.lib.layers.get_protected_layers")
    @patch("c2cgeoportal_geoportal.lib.layers.get_private_layers")
    def test_private_group_children_unauthorized(self, mock_private, mock_protected):
        """When a group is unauthorized, all its children are also unauthorized."""
        from c2cgeoportal_geoportal.lib.layers import get_unauthorized_layers

        layer = MagicMock()
        layer.layer = "private_group"
        mock_private.return_value = {1: layer}
        mock_protected.return_value = {}
        request = MagicMock()

        wms_children_map = {
            "private_group": ["child1", "child2"],
            "child1": ["grandchild1"],
        }

        result = get_unauthorized_layers(request, 1, wms_children_map)
        self.assertEqual(result, {"private_group", "child1", "child2", "grandchild1"})

    @patch("c2cgeoportal_geoportal.lib.layers.get_protected_layers")
    @patch("c2cgeoportal_geoportal.lib.layers.get_private_layers")
    def test_multiple_ogc_layers(self, mock_private, mock_protected):
        """A LayerWMS can reference multiple OGC layers."""
        from c2cgeoportal_geoportal.lib.layers import get_unauthorized_layers

        layer = MagicMock()
        layer.layer = "layer1,layer2"
        mock_private.return_value = {1: layer}
        mock_protected.return_value = {}
        request = MagicMock()

        result = get_unauthorized_layers(request, 1, {})
        self.assertEqual(result, {"layer1", "layer2"})

    @patch("c2cgeoportal_geoportal.lib.layers.get_protected_layers")
    @patch("c2cgeoportal_geoportal.lib.layers.get_private_layers")
    def test_layers_not_in_c2cgeoportal_are_public(self, mock_private, mock_protected):
        """Layers not defined in c2cgeoportal are considered public (not unauthorized)."""
        from c2cgeoportal_geoportal.lib.layers import get_unauthorized_layers

        layer = MagicMock()
        layer.layer = "defined_layer"
        mock_private.return_value = {1: layer}
        mock_protected.return_value = {}
        request = MagicMock()

        wms_children_map = {
            "defined_layer": ["child_defined"],
            "not_defined_group": ["child_not_defined"],
        }

        result = get_unauthorized_layers(request, 1, wms_children_map)
        self.assertIn("defined_layer", result)
        self.assertIn("child_defined", result)
        self.assertNotIn("not_defined_group", result)
        self.assertNotIn("child_not_defined", result)
