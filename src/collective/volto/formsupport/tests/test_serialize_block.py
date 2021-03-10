# -*- coding: utf-8 -*-
from collective.volto.formsupport.testing import (
    VOLTO_FORMSUPPORT_API_FUNCTIONAL_TESTING,  # noqa: E501,
)
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import SITE_OWNER_NAME
from plone.app.testing import SITE_OWNER_PASSWORD
from plone.app.testing import TEST_USER_ID
from plone.restapi.testing import RelativeSession

import transaction
import unittest


class TestBlockSerialization(unittest.TestCase):

    layer = VOLTO_FORMSUPPORT_API_FUNCTIONAL_TESTING

    def setUp(self):
        self.app = self.layer["app"]
        self.portal = self.layer["portal"]
        self.portal_url = self.portal.absolute_url()
        setRoles(self.portal, TEST_USER_ID, ["Manager"])

        self.api_session = RelativeSession(self.portal_url)
        self.api_session.headers.update({"Accept": "application/json"})
        self.api_session.auth = (SITE_OWNER_NAME, SITE_OWNER_PASSWORD)
        self.anon_api_session = RelativeSession(self.portal_url)
        self.anon_api_session.headers.update({"Accept": "application/json"})

        self.document = api.content.create(
            type="Document", title="Example context", container=self.portal,
        )
        self.document.blocks = {
            "text-id": {"@type": "text"},
            "form-id": {
                "@type": "form",
                "default_from": "foo@foo.com",
                "default_bar": "bar",
                "name": {},
                "surname": {},
            },
        }
        self.document_url = self.document.absolute_url()
        api.content.transition(obj=self.document, transition="publish")
        transaction.commit()

    def tearDown(self):
        self.api_session.close()
        self.anon_api_session.close()

    def test_serializer_return_full_block_data_to_admin(self):
        response = self.api_session.get(self.document_url)
        res = response.json()
        self.assertEqual(
            res["blocks"]["form-id"], self.document.blocks["form-id"]
        )

    def test_serializer_return_filtered_block_data_to_anon(self):
        response = self.anon_api_session.get(self.document_url)
        res = response.json()
        self.assertNotEqual(
            res["blocks"]["form-id"], self.document.blocks["form-id"]
        )
        self.assertNotIn("default_from", res["blocks"]["form-id"].keys())
        self.assertNotIn("default_foo", res["blocks"]["form-id"].keys())
        self.assertIn("name", res["blocks"]["form-id"].keys())
        self.assertIn("surname", res["blocks"]["form-id"].keys())
