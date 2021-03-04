# -*- coding: utf-8 -*-
"""Setup tests for this package."""
from collective.volto.formsupport.testing import (
    VOLTO_FORMSUPPORT_INTEGRATION_TESTING,  # noqa: E501,
)
from plone import api
from plone.app.testing import setRoles, TEST_USER_ID

import unittest


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
        self.assertTrue(
            self.installer.isProductInstalled("collective.volto.formsupport")
        )

    def test_browserlayer(self):
        """Test that ICollectiveVoltoFormsupportLayer is registered."""
        from collective.volto.formsupport.interfaces import (
            ICollectiveVoltoFormsupportLayer,
        )
        from plone.browserlayer import utils

        self.assertIn(
            ICollectiveVoltoFormsupportLayer, utils.registered_layers()
        )


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
        self.installer.uninstallProducts(["collective.volto.formsupport"])
        setRoles(self.portal, TEST_USER_ID, roles_before)

    def test_product_uninstalled(self):
        """Test if collective.volto.formsupport is cleanly uninstalled."""
        self.assertFalse(
            self.installer.isProductInstalled("collective.volto.formsupport")
        )

    def test_browserlayer_removed(self):
        """Test that ICollectiveVoltoFormsupportLayer is removed."""
        from collective.volto.formsupport.interfaces import (
            ICollectiveVoltoFormsupportLayer,
        )
        from plone.browserlayer import utils

        self.assertNotIn(
            ICollectiveVoltoFormsupportLayer, utils.registered_layers()
        )
