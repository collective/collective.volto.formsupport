# -*- coding: utf-8 -*-
import os
import unittest

import transaction
from plone import api
from plone.app.testing import (
    SITE_OWNER_NAME,
    SITE_OWNER_PASSWORD,
    TEST_USER_ID,
    setRoles,
)
from plone.registry.interfaces import IRegistry
from plone.restapi.testing import RelativeSession
from Products.MailHost.interfaces import IMailHost
from zope.component import getUtility

from collective.volto.formsupport.testing import (  # noqa: E501,
    VOLTO_FORMSUPPORT_API_FUNCTIONAL_TESTING,
)
from collective.volto.formsupport.validation import getValidations


class TestMailSend(unittest.TestCase):
    layer = VOLTO_FORMSUPPORT_API_FUNCTIONAL_TESTING

    def setUp(self):
        self.app = self.layer["app"]
        self.portal = self.layer["portal"]
        self.portal_url = self.portal.absolute_url()
        setRoles(self.portal, TEST_USER_ID, ["Manager"])

        self.mailhost = getUtility(IMailHost)

        registry = getUtility(IRegistry)
        registry["plone.email_from_address"] = "site_addr@plone.com"
        registry["plone.email_from_name"] = "Plone test site"

        self.api_session = RelativeSession(self.portal_url)
        self.api_session.headers.update({"Accept": "application/json"})
        self.api_session.auth = (SITE_OWNER_NAME, SITE_OWNER_PASSWORD)
        self.anon_api_session = RelativeSession(self.portal_url)
        self.anon_api_session.headers.update({"Accept": "application/json"})

        self.document = api.content.create(
            type="Document",
            title="Example context",
            container=self.portal,
        )
        self.document.blocks = {
            "text-id": {"@type": "text"},
            "form-id": {"@type": "form"},
        }
        self.document_url = self.document.absolute_url()
        transaction.commit()

    def tearDown(self):
        self.api_session.close()
        self.anon_api_session.close()

        # set default block
        self.document.blocks = {
            "text-id": {"@type": "text"},
            "form-id": {"@type": "form"},
        }

        os.environ["FORM_ATTACHMENTS_LIMIT"] = ""

        transaction.commit()

    def submit_form(self, data):
        url = "{}/@submit-form".format(self.document_url)
        response = self.api_session.post(
            url,
            json=data,
        )
        transaction.commit()
        return response

    def test_validation(self):
        self.document.blocks = {
            "text-id": {"@type": "text"},
            "form-id": {
                "@type": "form",
                "default_subject": "block subject",
                "default_from": "john@doe.com",
                "send": ["acknowledgement"],
                "acknowledgementFields": "contact",
                "acknowledgementMessage": {
                    "data": "<p>This message will be sent to the person filling in the form.</p><p>It is <strong>Rich Text</strong></p>"
                },
                "subblocks": [
                    {
                        "field_id": "123456789",
                        "field_type": "text",
                        "id": "123456789",
                        "inNumericRange": {"maxval": "7", "minval": "2"},
                        "label": "My field",
                        "required": False,
                        "show_when_when": "always",
                        "validationSettings": {"maxval": "7", "minval": "2"},
                        "validations": ["inNumericRange"],
                    }
                ],
            },
        }
        transaction.commit()

        response = self.api_session.get(self.document_url)
        res = response.json()

        validations = getValidations()
        breakpoint()
        self.assertEqual(res["blocks"]["form-id"], self.document.blocks["form-id"])

        # response = self.submit_form(
        #     data={
        #         "data": [{"field_id": "123456789", "value": "4", "label": "My field"}],
        #         "block_id": "form-id",
        #     },
        # )
        # transaction.commit()

        # breakpoint()
        # self.assertEqual(response.status_code, 204)

        # msg = self.mailhost.messages[0]
        # if isinstance(msg, bytes) and bytes is not str:
        #     # Python 3 with Products.MailHost 4.10+
        #     msg = msg.decode("utf-8")

        # parsed_msg = Parser().parse(StringIO(msg))
        # self.assertEqual(parsed_msg.get("from"), "john@doe.com")
        # self.assertEqual(parsed_msg.get("to"), "smith@doe.com")
        # self.assertEqual(parsed_msg.get("subject"), "block subject")
        # msg_body = parsed_msg.get_payload(decode=True).decode()
        # self.assertIn(
        #     "<p>This message will be sent to the person filling in the form.</p>",
        #     msg_body,
        # )
        # self.assertIn("<p>It is <strong>Rich Text</strong></p>", msg_body)
