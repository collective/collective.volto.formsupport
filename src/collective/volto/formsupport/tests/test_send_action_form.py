# -*- coding: utf-8 -*-
from collective.volto.formsupport.testing import (
    VOLTO_FORMSUPPORT_API_FUNCTIONAL_TESTING,  # noqa: E501,
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
        registry["plone.email_from_name"] = u"Plone test site"

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
        transaction.commit()

    def submit_form(self, data):
        url = "{}/@submit-form".format(self.document_url)
        response = self.api_session.post(
            url,
            json=data,
        )
        transaction.commit()
        return response

    def test_email_not_send_if_block_id_is_not_given(self):
        response = self.submit_form(
            data={"from": "john@doe.com", "message": "Just want to say hi."},
        )
        transaction.commit()

        res = response.json()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(res["message"], "Missing block_id")

    def test_email_not_send_if_block_id_is_incorrect_or_not_present(self):
        response = self.submit_form(
            data={
                "from": "john@doe.com",
                "message": "Just want to say hi.",
                "block_id": "unknown",
            },
        )
        transaction.commit()

        res = response.json()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            res["message"],
            'Block with @type "form" and id "unknown" not found in this context: {}'.format(  # noqa
                self.document_url
            ),
        )

        response = self.submit_form(
            data={
                "from": "john@doe.com",
                "message": "Just want to say hi.",
                "block_id": "text-id",
            },
        )
        transaction.commit()

        res = response.json()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            res["message"],
            'Block with @type "form" and id "text-id" not found in this context: {}'.format(  # noqa
                self.document_url
            ),
        )

    def test_email_not_send_if_no_action_set(self):

        response = self.submit_form(
            data={"from": "john@doe.com", "block_id": "form-id"},
        )
        transaction.commit()
        res = response.json()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            res["message"],
            'You need to set at least one form action between "send" and "store".',  # noqa
        )

    def test_email_not_send_if_block_id_is_correct_but_form_data_missing(
        self,
    ):

        self.document.blocks = {
            "form-id": {"@type": "form", "send": True},
        }
        transaction.commit()

        response = self.submit_form(
            data={
                "from": "john@doe.com",
                "subject": "test subject",
                "block_id": "form-id",
            },
        )
        transaction.commit()
        res = response.json()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            res["message"],
            "Empty form data.",
        )

    def test_email_not_send_if_block_id_is_correct_but_required_fields_missing(
        self,
    ):

        self.document.blocks = {
            "form-id": {"@type": "form", "send": True},
        }
        transaction.commit()

        response = self.submit_form(
            data={
                "from": "john@doe.com",
                "block_id": "form-id",
                "data": [{"label": "foo", "value": "bar"}],
            },
        )
        transaction.commit()
        res = response.json()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            res["message"],
            "Missing required field: subject or from.",
        )

    def test_email_sent_with_site_recipient(
        self,
    ):

        self.document.blocks = {
            "form-id": {"@type": "form", "send": True},
        }
        transaction.commit()

        response = self.submit_form(
            data={
                "from": "john@doe.com",
                "data": [
                    {"label": "Message", "value": "just want to say hi"},
                    {"label": "Name", "value": "John"},
                ],
                "subject": "test subject",
                "block_id": "form-id",
            },
        )
        transaction.commit()
        self.assertEqual(response.status_code, 204)
        msg = self.mailhost.messages[0]
        if isinstance(msg, bytes) and bytes is not str:
            # Python 3 with Products.MailHost 4.10+
            msg = msg.decode("utf-8")
        self.assertIn("Subject: test subject", msg)
        self.assertIn("From: john@doe.com", msg)
        self.assertIn("To: site_addr@plone.com", msg)
        self.assertIn("Reply-To: john@doe.com", msg)
        self.assertIn("<strong>Message:</strong> just want to say hi", msg)
        self.assertIn("<strong>Name:</strong> John", msg)

    def test_email_sent_ignore_passed_recipient(
        self,
    ):

        self.document.blocks = {
            "form-id": {"@type": "form", "send": True},
        }
        transaction.commit()

        response = self.submit_form(
            data={
                "from": "john@doe.com",
                "to": "to@spam.com",
                "data": [
                    {"label": "Message", "value": "just want to say hi"},
                    {"label": "Name", "value": "John"},
                ],
                "subject": "test subject",
                "block_id": "form-id",
            },
        )
        transaction.commit()
        self.assertEqual(response.status_code, 204)
        msg = self.mailhost.messages[0]
        if isinstance(msg, bytes) and bytes is not str:
            # Python 3 with Products.MailHost 4.10+
            msg = msg.decode("utf-8")
        self.assertIn("Subject: test subject", msg)
        self.assertIn("From: john@doe.com", msg)
        self.assertIn("To: site_addr@plone.com", msg)
        self.assertIn("Reply-To: john@doe.com", msg)
        self.assertIn("<strong>Message:</strong> just want to say hi", msg)
        self.assertIn("<strong>Name:</strong> John", msg)

    def test_email_sent_with_block_recipient_if_set(
        self,
    ):

        self.document.blocks = {
            "text-id": {"@type": "text"},
            "form-id": {
                "@type": "form",
                "default_to": "to@block.com",
                "send": True,
            },
        }
        transaction.commit()

        response = self.submit_form(
            data={
                "from": "john@doe.com",
                "data": [
                    {"label": "Message", "value": "just want to say hi"},
                    {"label": "Name", "value": "John"},
                ],
                "subject": "test subject",
                "block_id": "form-id",
            },
        )
        transaction.commit()
        self.assertEqual(response.status_code, 204)
        msg = self.mailhost.messages[0]
        if isinstance(msg, bytes) and bytes is not str:
            # Python 3 with Products.MailHost 4.10+
            msg = msg.decode("utf-8")
        self.assertIn("Subject: test subject", msg)
        self.assertIn("From: john@doe.com", msg)
        self.assertIn("To: to@block.com", msg)
        self.assertIn("Reply-To: john@doe.com", msg)
        self.assertIn("<strong>Message:</strong> just want to say hi", msg)
        self.assertIn("<strong>Name:</strong> John", msg)

    def test_email_sent_with_block_subject_if_set_and_not_passed(
        self,
    ):

        self.document.blocks = {
            "text-id": {"@type": "text"},
            "form-id": {
                "@type": "form",
                "default_subject": "block subject",
                "send": True,
            },
        }
        transaction.commit()

        response = self.submit_form(
            data={
                "from": "john@doe.com",
                "data": [
                    {"label": "Message", "value": "just want to say hi"},
                    {"label": "Name", "value": "John"},
                ],
                "block_id": "form-id",
            },
        )
        transaction.commit()

        self.assertEqual(response.status_code, 204)
        msg = self.mailhost.messages[0]
        if isinstance(msg, bytes) and bytes is not str:
            # Python 3 with Products.MailHost 4.10+
            msg = msg.decode("utf-8")
        self.assertIn("Subject: block subject", msg)
        self.assertIn("From: john@doe.com", msg)
        self.assertIn("To: site_addr@plone.com", msg)
        self.assertIn("Reply-To: john@doe.com", msg)
        self.assertIn("<strong>Message:</strong> just want to say hi", msg)
        self.assertIn("<strong>Name:</strong> John", msg)

    def test_email_with_use_as_reply_to(
        self,
    ):

        self.document.blocks = {
            "text-id": {"@type": "text"},
            "form-id": {
                "@type": "form",
                "default_subject": "block subject",
                "default_from": "john@doe.com",
                "send": True,
                "subblocks": [
                    {
                        "field_id": "contact",
                        "field_type": "from",
                        "use_as_reply_to": True,
                    },
                ],
            },
        }
        transaction.commit()

        response = self.submit_form(
            data={
                "data": [
                    {"label": "Message", "value": "just want to say hi"},
                    {"label": "Name", "value": "Smith"},
                    {"field_id": "contact", "label": "Email", "value": "smith@doe.com"},
                ],
                "block_id": "form-id",
            },
        )
        transaction.commit()

        self.assertEqual(response.status_code, 204)
        msg = self.mailhost.messages[0]
        if isinstance(msg, bytes) and bytes is not str:
            # Python 3 with Products.MailHost 4.10+
            msg = msg.decode("utf-8")
        self.assertIn("Subject: block subject", msg)
        self.assertIn("From: john@doe.com", msg)
        self.assertIn("To: site_addr@plone.com", msg)
        self.assertIn("Reply-To: smith@doe.com", msg)
        self.assertIn("<strong>Message:</strong> just want to say hi", msg)
        self.assertIn("<strong>Name:</strong> Smith", msg)
