"""Setup tests for this package."""

from collective.volto.formsupport import PACKAGE_NAME

import pytest


class TestSetup:
    """Test that collective.volto.formsupport is properly installed."""

    def test_product_installed(self, installer):
        """Test if collective.volto.formsupport is installed."""
        assert installer.is_product_installed(PACKAGE_NAME) is True

    def test_browserlayer(self, browser_layers):
        """Test that ICollectiveVoltoFormsupportLayer is registered."""
        from collective.volto.formsupport.interfaces import (
            ICollectiveVoltoFormsupportLayer,
        )

        assert ICollectiveVoltoFormsupportLayer in browser_layers


class TestUninstall:
    @pytest.fixture(autouse=True)
    def uninstalled(self, installer):
        installer.uninstall_product(PACKAGE_NAME)

    def test_product_uninstalled(self, installer):
        """Test if collective.volto.formsupport is cleanly uninstalled."""
        assert installer.is_product_installed(PACKAGE_NAME) is False

    def test_browserlayer_removed(self, browser_layers):
        """Test that ICollectiveVoltoFormsupportLayer is removed."""
        from collective.volto.formsupport.interfaces import (
            ICollectiveVoltoFormsupportLayer,
        )

        assert ICollectiveVoltoFormsupportLayer not in browser_layers
