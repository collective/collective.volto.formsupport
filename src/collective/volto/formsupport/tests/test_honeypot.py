# -*- coding: utf-8 -*-
from collective.volto.formsupport.testing import (  # noqa: E501,
    VOLTO_FORMSUPPORT_API_FUNCTIONAL_TESTING,
)
from hashlib import md5
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import SITE_OWNER_NAME
from plone.app.testing import SITE_OWNER_PASSWORD
from plone.app.testing import TEST_USER_ID
from plone.formwidget.hcaptcha.interfaces import IHCaptchaSettings
from plone.formwidget.recaptcha.interfaces import IReCaptchaSettings
from collective.z3cform.norobots.browser.interfaces import INorobotsWidgetSettings
from plone.registry.interfaces import IRegistry
from plone.restapi.testing import RelativeSession
from Products.MailHost.interfaces import IMailHost
from unittest.mock import Mock
from unittest.mock import patch
from zope.component import getUtility
from collective.honeypot.config import EXTRA_PROTECTED_ACTIONS

import json
import transaction
import unittest


class TestHoneypot(unittest.TestCase):

    layer = VOLTO_FORMSUPPORT_API_FUNCTIONAL_TESTING

    def setUp(self):
        self.app = self.layer["app"]
        self.portal = self.layer["portal"]
        self.portal_url = self.portal.absolute_url()
        setRoles(self.portal, TEST_USER_ID, ["Manager"])

        self.mailhost = getUtility(IMailHost)

        self.registry = getUtility(IRegistry)
        self.registry["plone.email_from_address"] = "site_addr@plone.com"
        self.registry["plone.email_from_name"] = "Plone test site"

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
        return response

    def test_honeypot_installed_but_field_not_in_form(self):

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
                        "use_as_bcc": True,
                    },
                ],
                "captcha": "honeypot",
            },
        }
        transaction.commit()
        response = self.submit_form(
            data={
                "data": [
                    {"label": "Message", "value": "just want to say hi"},
                ],
                "block_id": "form-id",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["message"],
            "Error submitting form.",
        )

    def test_honeypot_field_in_form_empty_pass_validation(self):

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
                        "use_as_bcc": True,
                    },
                ],
                "captcha": "honeypot",
            },
        }
        transaction.commit()
        response = self.submit_form(
            data={
                "data": [
                    {"label": "Message", "value": "just want to say hi"},
                    {"label": "protected_1", "value": ""},
                ],
                "block_id": "form-id",
            },
        )

        self.assertEqual(response.status_code, 204)

    def test_honeypot_field_in_form_compiled_fail_validation(self):

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
                        "use_as_bcc": True,
                    },
                ],
                "captcha": "honeypot",
            },
        }
        transaction.commit()
        response = self.submit_form(
            data={
                "data": [
                    {"label": "Message", "value": "just want to say hi"},
                    {"label": "protected_1", "value": "foo"},
                ],
                "block_id": "form-id",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["message"],
            "Error submitting form.",
        )
