from collective.volto.formsupport.testing import (  # noqa: E501,
    VOLTO_FORMSUPPORT_API_FUNCTIONAL_TESTING,
)
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import SITE_OWNER_NAME
from plone.app.testing import SITE_OWNER_PASSWORD
from plone.app.testing import TEST_USER_ID
from plone.registry.interfaces import IRegistry
from plone.restapi.testing import RelativeSession
from Products.MailHost.interfaces import IMailHost
from zope.component import getUtility

import transaction
import unittest


class TestHoneypotField(unittest.TestCase):
    """The "honeypot" option of the form block: a hidden website field."""

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
        api.content.transition(obj=self.document, transition="publish")
        self.document_url = self.document.absolute_url()
        self.set_form(honeypot=True)

    def tearDown(self):
        self.api_session.close()
        self.anon_api_session.close()

    def set_form(self, honeypot):
        self.document.blocks = {
            "text-id": {"@type": "text"},
            "form-id": {
                "@type": "form",
                "default_subject": "block subject",
                "default_from": "john@doe.com",
                "send": ["recipient"],
                "store": True,
                "honeypot": honeypot,
                "subblocks": [
                    {
                        "field_id": "message",
                        "field_type": "text",
                    },
                ],
            },
        }
        transaction.commit()

    def submit_form(self, **extra):
        response = self.anon_api_session.post(
            f"{self.document_url}/@submit-form",
            json={
                "data": [
                    {
                        "field_id": "message",
                        "label": "Message",
                        "value": "just want to say hi",
                    },
                ],
                "block_id": "form-id",
                **extra,
            },
        )
        transaction.commit()
        return response

    def stored_items(self):
        response = self.api_session.get(f"{self.document_url}/@form-data")
        return response.json()["items"]

    def test_honeypot_filled_in(self):
        with self.assertLogs(
            "collective.volto.formsupport.restapi.services.submit_form.post", "INFO"
        ) as logs:
            response = self.submit_form(website="https://spam.example.org")
        # Answered as sent, but nothing is sent or stored.
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.mailhost.messages, [])
        self.assertEqual(self.stored_items(), [])
        # Logged to count them, without the value.
        self.assertIn(
            "Spam blocked: reason=honeypot form=/plone/example-context block=form-id",
            logs.output[-1],
        )
        self.assertNotIn("spam.example.org", "\n".join(logs.output))

    def test_honeypot_empty(self):
        response = self.submit_form(website="")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(self.mailhost.messages), 1)
        self.assertEqual(len(self.stored_items()), 1)

    def test_honeypot_not_sent(self):
        response = self.submit_form()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(self.mailhost.messages), 1)

    def test_honeypot_option_off(self):
        # Without the option, the website key means nothing.
        self.set_form(honeypot=False)
        response = self.submit_form(website="https://www.example.org")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(self.mailhost.messages), 1)
