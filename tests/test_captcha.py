from collective.z3cform.norobots.browser.interfaces import INorobotsWidgetSettings
from hashlib import md5
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.formwidget.hcaptcha.interfaces import IHCaptchaSettings
from plone.formwidget.recaptcha.interfaces import IReCaptchaSettings
from plone.registry.interfaces import IRegistry
from Products.MailHost.interfaces import IMailHost
from unittest.mock import Mock
from unittest.mock import patch
from zope.component import getUtility

import json
import pytest
import transaction


pytest_plugins = ["pytest_plone"]


@pytest.mark.usefixtures("functional")
class TestCaptcha:
    @pytest.fixture(autouse=True)
    def setup(self, functional):
        from plone.app.testing import SITE_OWNER_NAME, SITE_OWNER_PASSWORD
        from plone.restapi.testing import RelativeSession

        # Get app and portal from the functional layer
        self.app = functional["app"]
        self.portal = functional["portal"]
        self.portal_url = self.portal.absolute_url()

        setRoles(self.portal, TEST_USER_ID, ["Manager"])

        self.mailhost = getUtility(IMailHost)

        self.registry = getUtility(IRegistry)
        self.registry["plone.email_from_address"] = "site_addr@plone.com"
        self.registry["plone.email_from_name"] = "Plone test site"

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

        # Create API session
        self.api_session = RelativeSession(self.portal_url)
        self.api_session.headers.update({"Accept": "application/json"})
        self.api_session.auth = (SITE_OWNER_NAME, SITE_OWNER_PASSWORD)

        yield

        self.api_session.close()

        # tearDown
        self.document.blocks = {
            "text-id": {"@type": "text"},
            "form-id": {"@type": "form"},
        }
        transaction.commit()

    def submit_form(self, data):
        url = f"{self.document_url}/@submit-form"
        response = self.api_session.post(
            url,
            json=data,
        )
        return response

    def test_recaptcha_no_settings(self):
        self.document.blocks = {
            "text-id": {"@type": "text"},
            "form-id": {
                "@type": "form",
                "default_subject": "block subject",
                "default_from": "john@doe.com",
                "send": ["recipient"],
                "subblocks": [
                    {
                        "field_id": "contact",
                        "field_type": "from",
                        "use_as_bcc": True,
                    },
                    {
                        "field_id": "message",
                        "field_type": "text",
                    },
                ],
                "captcha": "recaptcha",
            },
        }
        self.registry.registerInterface(IReCaptchaSettings)
        transaction.commit()
        response = self.submit_form(
            data={
                "data": [
                    {
                        "field_id": "message",
                        "label": "Message",
                        "value": "just want to say hi",
                    },
                ],
                "block_id": "form-id",
            },
        )
        transaction.commit()
        assert response.status_code == 500
        assert response.json()["message"] == (
            "No recaptcha private key configured. Go to path/to/site/@@recaptcha-settings "
            "to configure."
        )

    def test_recaptcha(self):
        self.registry.registerInterface(IReCaptchaSettings)
        settings = self.registry.forInterface(IReCaptchaSettings)
        settings.public_key = "public"
        settings.private_key = "private"

        self.document.blocks = {
            "text-id": {"@type": "text"},
            "form-id": {
                "@type": "form",
                "default_subject": "block subject",
                "default_from": "john@doe.com",
                "send": ["recipient"],
                "subblocks": [
                    {
                        "field_id": "contact",
                        "field_type": "from",
                        "use_as_bcc": True,
                    },
                    {
                        "field_id": "message",
                        "field_type": "text",
                    },
                ],
                "captcha": "recaptcha",
            },
        }
        transaction.commit()

        response = self.submit_form(
            data={
                "data": [
                    {
                        "field_id": "message",
                        "label": "Message",
                        "value": "just want to say hi",
                    },
                ],
                "block_id": "form-id",
            },
        )
        transaction.commit()
        assert response.status_code == 400
        assert response.json()["message"] == "No captcha token provided."

        with patch(
            "collective.volto.formsupport.captcha.recaptcha.submit"
        ) as mock_submit:
            mock_submit.return_value = Mock(is_valid=False)
            response = self.submit_form(
                data={
                    "data": [
                        {
                            "field_id": "message",
                            "label": "Message",
                            "value": "just want to say hi",
                        },
                    ],
                    "block_id": "form-id",
                    "captcha": {"token": "12345"},
                },
            )
            transaction.commit()
            mock_submit.assert_called_once_with("12345", "private", "127.0.0.1")
            assert response.status_code == 400
            assert response.json()["message"] == (
                "The code you entered was wrong, please enter the new one."
            )

        with patch(
            "collective.volto.formsupport.captcha.recaptcha.submit"
        ) as mock_submit:
            mock_submit.return_value = Mock(is_valid=True)
            response = self.submit_form(
                data={
                    "data": [
                        {
                            "field_id": "message",
                            "label": "Message",
                            "value": "just want to say hi",
                        },
                    ],
                    "block_id": "form-id",
                    "captcha": {"token": "12345"},
                },
            )
            transaction.commit()
            mock_submit.assert_called_once_with("12345", "private", "127.0.0.1")
            assert response.status_code == 200

    def test_hcaptcha(self):
        self.registry.registerInterface(IHCaptchaSettings)
        settings = self.registry.forInterface(IHCaptchaSettings)
        settings.public_key = "public"
        settings.private_key = "private"

        self.document.blocks = {
            "text-id": {"@type": "text"},
            "form-id": {
                "@type": "form",
                "default_subject": "block subject",
                "default_from": "john@doe.com",
                "send": ["recipient"],
                "subblocks": [
                    {
                        "field_id": "contact",
                        "field_type": "from",
                        "use_as_bcc": True,
                    },
                    {
                        "field_id": "message",
                        "field_type": "text",
                    },
                ],
                "captcha": "hcaptcha",
            },
        }
        transaction.commit()

        response = self.submit_form(
            data={
                "data": [
                    {
                        "field_id": "message",
                        "label": "Message",
                        "value": "just want to say hi",
                    },
                ],
                "block_id": "form-id",
            },
        )
        transaction.commit()
        assert response.status_code == 400
        assert response.json()["message"] == "No captcha token provided."

        with patch(
            "collective.volto.formsupport.captcha.hcaptcha.submit"
        ) as mock_submit:
            mock_submit.return_value = Mock(is_valid=False)
            response = self.submit_form(
                data={
                    "data": [
                        {
                            "field_id": "message",
                            "label": "Message",
                            "value": "just want to say hi",
                        },
                    ],
                    "block_id": "form-id",
                    "captcha": {"token": "12345"},
                },
            )
            transaction.commit()
            mock_submit.assert_called_once_with("12345", "private")
            assert response.status_code == 400
            assert response.json()["message"] == (
                "The code you entered was wrong, please enter the new one."
            )

        with patch(
            "collective.volto.formsupport.captcha.hcaptcha.submit"
        ) as mock_submit:
            mock_submit.return_value = Mock(is_valid=True)
            response = self.submit_form(
                data={
                    "data": [
                        {
                            "field_id": "message",
                            "label": "Message",
                            "value": "just want to say hi",
                        },
                    ],
                    "block_id": "form-id",
                    "captcha": {"token": "12345"},
                },
            )
            transaction.commit()
            mock_submit.assert_called_once_with("12345", "private")
            assert response.status_code == 200

    def test_get_vocabulary(self):
        response = self.api_session.get(
            "/@vocabularies/collective.volto.formsupport.captcha.providers"
        )
        assert response.status_code == 200
        data = response.json()
        # no adapters configured
        assert data["@id"].endswith(
            "@vocabularies/collective.volto.formsupport.captcha.providers"
        )

        # honeypot is always active if it's in buildout
        assert data["items_total"] == 1
        assert data["items"] == [{"title": "Honeypot Support", "token": "honeypot"}]

        # configure recaptcha
        self.registry.registerInterface(IReCaptchaSettings)
        settings = self.registry.forInterface(IReCaptchaSettings)
        settings.public_key = "public"
        settings.private_key = "private"
        transaction.commit()
        response = self.api_session.get(
            "/@vocabularies/collective.volto.formsupport.captcha.providers"
        )
        assert response.status_code == 200
        data = response.json()
        # no adapters configured
        assert data["@id"].endswith(
            "@vocabularies/collective.volto.formsupport.captcha.providers"
        )
        assert data["items_total"] == 2
        assert data["items"] == [
            {"title": "Google ReCaptcha", "token": "recaptcha"},
            {"title": "Honeypot Support", "token": "honeypot"},
        ]

    def test_norobots(self):
        """test that using norobots the captcha can be passed"""
        self.registry.registerInterface(INorobotsWidgetSettings)
        settings = self.registry.forInterface(INorobotsWidgetSettings)
        settings.questions = ("Write five using ciphers::5", "How much is 10 + 4::14")
        transaction.commit()

        self.document.blocks = {
            "text-id": {"@type": "text"},
            "form-id": {
                "@type": "form",
                "default_subject": "block subject",
                "default_from": "john@doe.com",
                "send": ["recipient"],
                "subblocks": [
                    {
                        "field_id": "contact",
                        "field_type": "from",
                        "use_as_bcc": True,
                    },
                    {
                        "field_id": "message",
                        "field_type": "text",
                    },
                ],
                "captcha": "norobots-captcha",
            },
        }
        transaction.commit()

        captcha_token = json.dumps({
            "value": "5",
            "id": "question0",
            "id_check": md5(  # noqa: S324
                "Write five using ciphers".encode("ascii", "ignore")
            ).hexdigest(),
        })

        response = self.submit_form(
            data={
                "data": [
                    {
                        "field_id": "message",
                        "label": "Message",
                        "value": "just want to say hi",
                    },
                ],
                "block_id": "form-id",
                "captcha": {"provider": "norobots-captcha", "token": captcha_token},
            },
        )
        assert response.status_code == 200

    def test_norobots_wrong_captcha(self):
        """test that using norobots and a wrong answer, the captcha is not passed"""
        self.registry.registerInterface(INorobotsWidgetSettings)
        settings = self.registry.forInterface(INorobotsWidgetSettings)
        settings.questions = ("Write five using ciphers::5", "How much is 10 + 4::14")
        transaction.commit()

        self.document.blocks = {
            "text-id": {"@type": "text"},
            "form-id": {
                "@type": "form",
                "default_subject": "block subject",
                "default_from": "john@doe.com",
                "send": ["recipient"],
                "subblocks": [
                    {
                        "field_id": "contact",
                        "field_type": "from",
                        "use_as_bcc": True,
                    },
                    {
                        "field_id": "message",
                        "field_type": "text",
                    },
                ],
                "captcha": "norobots-captcha",
            },
        }
        transaction.commit()

        captcha_token = json.dumps({
            "value": "15",
            "id": "question0",
            "id_check": md5(  # noqa: S324
                "Write five using ciphers".encode("ascii", "ignore")
            ).hexdigest(),
        })

        response = self.submit_form(
            data={
                "data": [
                    {
                        "field_id": "message",
                        "label": "Message",
                        "value": "just want to say hi",
                    },
                ],
                "block_id": "form-id",
                "captcha": {"provider": "norobots-captcha", "token": captcha_token},
            },
        )

        assert response.status_code == 400
        assert response.json()["message"] == (
            "The code you entered was wrong, please enter the new one."
        )
