from plone import api
from plone.app.testing import setRoles
from plone.app.testing import SITE_OWNER_NAME
from plone.app.testing import SITE_OWNER_PASSWORD
from plone.app.testing import TEST_USER_ID
from plone.registry.interfaces import IRegistry
from plone.restapi.testing import RelativeSession
from Products.MailHost.interfaces import IMailHost
from zope.component import getUtility
from zope.configuration import xmlconfig

import re
import sys

import pytest
import transaction


def event_handler(event):
    event.data["data"].append(
        {"label": "Reply", "value": "hello", "field_id": "message"},
    )


sys.modules.setdefault(
    "collective.volto.formsupport.tests.test_event",
    sys.modules[__name__],
)


pytest_plugins = ["pytest_plone"]


@pytest.mark.usefixtures("functional")
class TestEvent:
    @pytest.fixture(autouse=True)
    def setup(self, functional):
        xmlconfig.string(
            """
            <configure xmlns="http://namespaces.zope.org/zope">
                <subscriber
                    for="collective.volto.formsupport.interfaces.IPostEvent"
                    handler="collective.volto.formsupport.tests.test_event.event_handler"
                    />
            </configure>
        """,
            context=functional["configurationContext"],
        )
        self.app = functional["app"]
        self.portal = functional["portal"]
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

        yield

        self.api_session.close()
        self.anon_api_session.close()

        # set default block
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

    def test_trigger_event(self):
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

        assert response.status_code == 200
        assert len(self.mailhost.messages) == 1
        msg = self.mailhost.messages[0]
        if isinstance(msg, bytes) and bytes is not str:
            # Python 3 with Products.MailHost 4.10+
            msg = msg.decode("utf-8")
        msg = re.sub(r"\s+", " ", msg)
        assert "To: site_addr@plone.com" in msg
        assert "To: smith@doe.com" not in msg
        assert "<strong>Message:</strong> just want to say hi" in msg
        assert "<strong>Reply:</strong> hello" in msg
