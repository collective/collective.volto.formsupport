# -*- coding: utf-8 -*-
"""Setup tests for this package."""
import unittest

from plone import api
from plone.app.testing import TEST_USER_ID, setRoles

from collective.volto.formsupport.testing import (  # noqa: E501,
    VOLTO_FORMSUPPORT_INTEGRATION_TESTING,
)

try:
    from Products.CMFPlone.utils import get_installer
except ImportError:
    get_installer = None


class TestSetup(unittest.TestCase):
    """Test that collective.volto.formsupport is properly installed."""

    layer = VOLTO_FORMSUPPORT_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer["portal"]
        if get_installer:
            self.installer = get_installer(self.portal, self.layer["request"])
        else:
            self.installer = api.portal.get_tool("portal_quickinstaller")

    def test_product_installed(self):
        """Test if collective.volto.formsupport is installed."""
        if hasattr(self.installer, "isProductInstalled"):
            self.assertTrue(
                self.installer.isProductInstalled("collective.volto.formsupport")
            )
        else:  # plone 6
            self.assertTrue(
                self.installer.is_product_installed("collective.volto.formsupport")
            )

    def test_browserlayer(self):
        """Test that ICollectiveVoltoFormsupportLayer is registered."""
        from plone.browserlayer import utils

        from collective.volto.formsupport.interfaces import (
            ICollectiveVoltoFormsupportLayer,
        )

        self.assertIn(ICollectiveVoltoFormsupportLayer, utils.registered_layers())


class TestUninstall(unittest.TestCase):
    layer = VOLTO_FORMSUPPORT_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        if get_installer:
            self.installer = get_installer(self.portal, self.layer["request"])
        else:
            self.installer = api.portal.get_tool("portal_quickinstaller")
        roles_before = api.user.get_roles(TEST_USER_ID)
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        if hasattr(self.installer, "uninstallProducts"):
            self.installer.uninstallProducts(["collective.volto.formsupport"])
        else:  # plone6
            self.installer.uninstall_product("collective.volto.formsupport")
        setRoles(self.portal, TEST_USER_ID, roles_before)

    def test_product_uninstalled(self):
        """Test if collective.volto.formsupport is cleanly uninstalled."""
        if hasattr(self.installer, "isProductInstalled"):
            self.assertFalse(
                self.installer.isProductInstalled("collective.volto.formsupport")
            )
        else:  # plone 6
            self.assertFalse(
                self.installer.is_product_installed("collective.volto.formsupport")
            )

    def test_browserlayer_removed(self):
        """Test that ICollectiveVoltoFormsupportLayer is removed."""
        from plone.browserlayer import utils

        from collective.volto.formsupport.interfaces import (
            ICollectiveVoltoFormsupportLayer,
        )

        self.assertNotIn(ICollectiveVoltoFormsupportLayer, utils.registered_layers())
