from collective.volto.formsupport import form_token
from collective.volto.formsupport.testing import (  # noqa: E501,
    VOLTO_FORMSUPPORT_API_FUNCTIONAL_TESTING,
)
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.registry.interfaces import IRegistry
from plone.restapi import form_token as restapi_form_token
from plone.restapi.testing import RelativeSession
from Products.MailHost.interfaces import IMailHost
from unittest.mock import patch
from zope.component import getUtility

import os
import transaction
import unittest


class FakeMemcache:
    """The part of pymemcache's HashClient that plone.restapi.form_token uses."""

    def __init__(self):
        self.data = {}
        self.working = True

    def set(self, key, value, expire=0, noreply=None):
        if not self.working:
            return False
        self.data[key] = value.encode()
        return True

    def get(self, key):
        return self.data.get(key)

    def delete(self, key, noreply=None):
        return self.data.pop(key, None) is not None


class TestFormToken(unittest.TestCase):
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

        self.memcache = FakeMemcache()
        self.patches = [
            patch.dict(os.environ, {"FORM_TOKEN_MEMCACHE": "memcached:11211"}),
            patch.object(restapi_form_token, "get_client", lambda: self.memcache),
        ]
        for p in self.patches:
            p.start()

        self.anon_api_session = RelativeSession(self.portal_url)
        self.anon_api_session.headers.update({"Accept": "application/json"})

        self.document = api.content.create(
            type="Document",
            title="Example context",
            container=self.portal,
        )
        # A form without a captcha: the token is there for every form.
        self.document.blocks = {
            "text-id": {"@type": "text"},
            "form-id": {
                "@type": "form",
                "default_subject": "block subject",
                "default_from": "john@doe.com",
                "send": ["recipient"],
                "subblocks": [
                    {
                        "field_id": "message",
                        "field_type": "text",
                    },
                ],
            },
        }
        # The visitors who use the token are anonymous.
        api.content.transition(obj=self.document, transition="publish")
        self.document_url = self.document.absolute_url()
        transaction.commit()

    def tearDown(self):
        self.anon_api_session.close()
        for p in self.patches:
            p.stop()

    def get_token(self, age=None):
        """Get a token from @form-token, issued `age` seconds ago."""
        response = self.anon_api_session.get(f"{self.document_url}/@form-token")
        token = response.json()["token"]
        if age is None:
            age = form_token.get_min_age()
        key = restapi_form_token.KEY_PREFIX + token
        self.memcache.data[key] = str(int(self.memcache.data[key]) - age).encode()
        return token

    def submit_form(self, token=None, captcha=None):
        data = {
            "data": [
                {
                    "field_id": "message",
                    "label": "Message",
                    "value": "just want to say hi",
                },
            ],
            "block_id": "form-id",
        }
        if token is not None:
            data["form_token"] = token
        if captcha is not None:
            data["captcha"] = captcha
        response = self.anon_api_session.post(
            f"{self.document_url}/@submit-form", json=data
        )
        transaction.commit()
        return response

    def test_serialize(self):
        response = self.anon_api_session.get(self.document_url)
        block = response.json()["blocks"]["form-id"]
        self.assertEqual(block["form_token"], {"min_age": 15})
        self.assertNotIn("captcha_props", block)

    def test_not_a_captcha_provider(self):
        response = self.anon_api_session.get(
            "@vocabularies/collective.volto.formsupport.captcha.providers"
        )
        tokens = [item["token"] for item in response.json()["items"]]
        self.assertNotIn("token", tokens)

    def test_form_token(self):
        response = self.anon_api_session.get(f"{self.document_url}/@form-token")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Cache-Control"], "no-store, private")
        token = response.json()["token"]
        self.assertTrue(restapi_form_token.TOKEN_PATTERN.match(token))
        self.assertIn(restapi_form_token.KEY_PREFIX + token, self.memcache.data)

    def test_form_token_memcached_down(self):
        self.memcache.working = False
        response = self.anon_api_session.get(f"{self.document_url}/@form-token")
        self.assertEqual(response.status_code, 503)

    def test_submit_without_token(self):
        response = self.submit_form()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["message"], "Invalid request.")
        self.assertEqual(self.mailhost.messages, [])

    def test_submit_unknown_token(self):
        response = self.submit_form("x" * 43)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["message"], "Invalid request.")

    def test_submit_token_once(self):
        token = self.get_token()
        response = self.submit_form(token)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(self.mailhost.messages), 1)
        response = self.submit_form(token)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["message"], "Invalid request.")

    def test_submit_token_too_new(self):
        token = self.get_token(age=form_token.get_min_age() - 2)
        with self.assertLogs(restapi_form_token.logger, level="INFO") as logs:
            response = self.submit_form(token)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["message"], "Invalid request.")
        self.assertEqual(
            logs.output,
            [
                "INFO:plone.restapi.form_token:Spam blocked: "
                "reason=early-token form=/plone/example-context block=form-id"
            ],
        )
        # The token is used up: waiting does not help.
        self.assertEqual(self.memcache.data, {})

    def test_submit_with_captcha(self):
        # The token is checked next to the captcha of the form.
        self.document.blocks["form-id"]["captcha"] = "honeypot"
        self.document.blocks = dict(self.document.blocks)
        transaction.commit()
        captcha = {"provider": "honeypot", "value": ""}
        response = self.submit_form(captcha=captcha)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["message"], "Invalid request.")
        response = self.submit_form(self.get_token(), captcha=captcha)
        self.assertEqual(response.status_code, 200)

    def test_min_age_setting(self):
        with patch.dict(os.environ, {"FORM_TOKEN_MIN_AGE": "0"}):
            response = self.submit_form(self.get_token(age=0))
        self.assertEqual(response.status_code, 200)

    def test_not_configured(self):
        with patch.dict(os.environ, {"FORM_TOKEN_MEMCACHE": ""}):
            block = self.anon_api_session.get(self.document_url).json()["blocks"]
            self.assertNotIn("form_token", block["form-id"])
            response = self.submit_form()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(self.mailhost.messages), 1)

    def test_pymemcache_not_installed(self):
        with patch.object(restapi_form_token, "HashClient", None):
            block = self.anon_api_session.get(self.document_url).json()["blocks"]
            self.assertNotIn("form_token", block["form-id"])
            response = self.submit_form()
        self.assertEqual(response.status_code, 200)

    def test_restapi_without_form_tokens(self):
        with patch.object(form_token, "restapi_form_token", None):
            block = self.anon_api_session.get(self.document_url).json()["blocks"]
            self.assertNotIn("form_token", block["form-id"])
            response = self.submit_form()
        self.assertEqual(response.status_code, 200)
