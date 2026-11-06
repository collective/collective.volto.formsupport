from collective.volto.formsupport.interfaces import IPostAdapter
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from zope.component import getMultiAdapter

import pytest


pytest_plugins = ["pytest_plone"]


@pytest.mark.usefixtures("integration")
class TestFormDataAdapter:
    @pytest.fixture(autouse=True)
    def setup(self, integration):
        self.app = integration["app"]
        self.portal = integration["portal"]
        self.request = integration["request"]
        self.portal_url = self.portal.absolute_url()
        setRoles(self.portal, TEST_USER_ID, ["Manager"])

        self.document = api.content.create(
            type="Document",
            title="Example context",
            container=self.portal,
        )
        self.document.blocks = {
            "form-id": {
                "@type": "form",
                "send": ["recipient"],
                "subblocks": [
                    {
                        "field_id": "xxx",
                        "field_type": "text",
                    },
                ],
            }
        }

    def test_format_fields_join_list_values(self):
        self.request["BODY"] = (
            b'{"data": [{"field_id": "xxx", "value": ["a", "b"]}], "block_id": "form-id"}'
        )
        adapter = getMultiAdapter((self.document, self.request), IPostAdapter)

        assert adapter.format_fields()[0]["value"] == "a, b"
