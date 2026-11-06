from datetime import datetime
from io import StringIO
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import SITE_OWNER_NAME
from plone.app.testing import SITE_OWNER_PASSWORD
from plone.app.testing import TEST_USER_ID
from plone.restapi.testing import RelativeSession
from plone.testing.zope import Browser
from Products.MailHost.interfaces import IMailHost
from zope.component import getUtility

import base64
import csv
from pathlib import Path
import re
import transaction

import pytest


pytest_plugins = ["pytest_plone"]


FIXTURES_DIR = Path(__file__).resolve().parent


@pytest.mark.usefixtures("functional")
class TestMailStore:
    @pytest.fixture(autouse=True)
    def setup(self, functional):
        self.app = functional["app"]
        self.portal = functional["portal"]
        self.portal_url = self.portal.absolute_url()
        self.browser = Browser(functional["app"])

        setRoles(self.portal, TEST_USER_ID, ["Manager"])

        self.mailhost = getUtility(IMailHost)

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

        # tearDown
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
        transaction.commit()
        return response

    def export_data(self):
        url = f"{self.document_url}/@form-data"
        response = self.api_session.get(url)
        return response

    def export_csv(self):
        url = f"{self.document_url}/@form-data-export"
        response = self.api_session.get(url)
        return response

    def clear_data(self):
        url = f"{self.document_url}/@form-data-clear"
        response = self.api_session.delete(url)
        return response

    def test_unable_to_store_data(self):
        """form schema not defined, unable to store data"""
        self.document.blocks = {
            "form-id": {
                "@type": "form",
                "store": True,
            },
        }
        transaction.commit()

        response = self.submit_form(
            data={
                "from": "john@doe.com",
                "data": [
                    {
                        "field_id": "message",
                        "label": "Message",
                        "value": "just want to say hi",
                    },
                    {"field_id": "name", "label": "Name", "value": "John"},
                ],
                "subject": "test subject",
                "block_id": "form-id",
            },
        )
        transaction.commit()
        assert response.status_code == 400
        assert response.json()["message"] == "Empty form data."
        response = self.export_csv()

    def test_store_data(self):
        self.document.blocks = {
            "form-id": {
                "@type": "form",
                "store": True,
                "subblocks": [
                    {
                        "label": "Message",
                        "field_id": "message",
                        "field_type": "text",
                    },
                    {
                        "label": "Name",
                        "field_id": "name",
                        "field_type": "text",
                    },
                    {
                        "label": "Attachment",
                        "field_id": "file",
                        "field_type": "attachment",
                    },
                ],
            },
        }
        transaction.commit()

        filename = FIXTURES_DIR / "file.pdf"
        with filename.open("rb") as f:
            file_str = f.read()

        # TODO: test attachments with different content-type, encoding, and filename
        response = self.submit_form(
            data={
                "from": "john@doe.com",
                "data": [
                    {"field_id": "message", "value": "just want to say hi"},
                    {"field_id": "name", "value": "John"},
                    {"field_id": "foo", "value": "skip this"},
                ],
                "subject": "test subject",
                "block_id": "form-id",
                "attachments": {
                    "file_1": {
                        "field_id": "file",
                        "encoding": "base64",
                        "data": base64.b64encode(file_str),
                        "filename": "file.pdf",
                        "content-type": "application/pdf",
                    },
                },
            },
        )
        assert response.status_code == 200

        response = self.export_data()
        data = response.json()
        assert len(data["items"]) == 1
        assert sorted(data["items"][0].keys()) == [
            "__expired",
            "block_id",
            "date",
            "file",
            "id",
            "message",
            "name",
        ]
        assert data["items"][0]["message"] == {
            "label": "Message",
            "value": "just want to say hi",
            "field_type": "text",
        }
        assert data["items"][0]["name"] == {
            "label": "Name",
            "value": "John",
            "field_type": "text",
        }
        response = self.submit_form(
            data={
                "from": "sally@doe.com",
                "data": [
                    {"field_id": "message", "value": "bye"},
                    {"field_id": "name", "value": "Sally"},
                ],
                "subject": "test subject",
                "block_id": "form-id",
            },
        )
        transaction.commit()
        assert response.status_code == 200
        response = self.export_data()
        data = response.json()
        assert len(data["items"]) == 2
        assert sorted(data["items"][0].keys()) == [
            "__expired",
            "block_id",
            "date",
            "id",
            "message",
            "name",
        ]
        assert sorted(data["items"][1].keys()) == [
            "__expired",
            "block_id",
            "date",
            "file",
            "id",
            "message",
            "name",
        ]
        # sorted_data = sorted(data["items"], key=lambda x: x["name"]["value"])
        assert data["items"][0]["name"]["value"] == "Sally"
        assert data["items"][0]["message"]["value"] == "bye"

        assert data["items"][1]["name"]["value"] == "John"
        assert data["items"][1]["message"]["value"] == "just want to say hi"

        assert data["items"][1]["file"]["value"]["contentType"] == "application/pdf"
        assert data["items"][1]["file"]["value"]["filename"] == "file.pdf"
        assert data["items"][1]["file"]["value"]["size"] == 74429
        assert re.search(
            r"/example-context/saved_data/@@download/[0-9]+/file/file.pdf$",
            data["items"][1]["file"]["value"]["url"],
        )

        # get file
        self.browser.addHeader(
            "Authorization",
            f"Basic {SITE_OWNER_NAME}:{SITE_OWNER_PASSWORD}",
        )
        self.browser.open(
            data["items"][1]["file"]["value"]["url"],
        )
        assert self.browser._response.status == "200 OK"
        assert self.browser.contents == file_str

        # clear data
        response = self.clear_data()
        assert response.status_code == 204
        response = self.export_csv()
        data = [*csv.reader(StringIO(response.text), delimiter=",")]
        assert len(data) == 1
        assert "date" in data[0]

    def test_export_csv(self):
        self.document.blocks = {
            "form-id": {
                "@type": "form",
                "store": True,
                "subblocks": [
                    {
                        "label": "Message",
                        "field_id": "message",
                        "field_type": "text",
                    },
                    {
                        "label": "Name",
                        "field_id": "name",
                        "field_type": "text",
                    },
                ],
            },
        }
        transaction.commit()
        response = self.submit_form(
            data={
                "from": "john@doe.com",
                "data": [
                    {"field_id": "message", "value": "just want to say hi"},
                    {"field_id": "name", "value": "John"},
                    {"field_id": "foo", "value": "skip this"},
                ],
                "subject": "test subject",
                "block_id": "form-id",
            },
        )

        response = self.submit_form(
            data={
                "from": "sally@doe.com",
                "data": [
                    {"field_id": "message", "value": "bye"},
                    {"field_id": "name", "value": "Sally"},
                ],
                "subject": "test subject",
                "block_id": "form-id",
            },
        )

        assert response.status_code == 200
        response = self.export_csv()
        data = [*csv.reader(StringIO(response.text), delimiter=",")]
        assert len(data) == 3
        assert data[0] == ["Message", "Name", "date"]
        sorted_data = sorted(data[1:])
        assert sorted_data[0][:-1] == ["bye", "Sally"]
        assert sorted_data[1][:-1] == ["just want to say hi", "John"]

        # check date column. Skip seconds because can change during test
        now = datetime.now().strftime("%Y-%m-%dT%H:%M")
        assert sorted_data[0][-1].startswith(now)
        assert sorted_data[1][-1].startswith(now)

    def test_data_id_mapping(self):
        self.document.blocks = {
            "form-id": {
                "@type": "form",
                "store": True,
                "test-field": "renamed-field",
                "subblocks": [
                    {
                        "field_id": "message",
                        "label": "Message",
                        "field_type": "text",
                    },
                    {
                        "field_id": "test-field",
                        "label": "Test field",
                        "field_type": "text",
                    },
                ],
            },
        }
        transaction.commit()
        response = self.submit_form(
            data={
                "from": "john@doe.com",
                "data": [
                    {"field_id": "message", "value": "just want to say hi"},
                    {"field_id": "test-field", "value": "John"},
                ],
                "subject": "test subject",
                "block_id": "form-id",
            },
        )

        response = self.submit_form(
            data={
                "from": "sally@doe.com",
                "data": [
                    {"field_id": "message", "value": "bye"},
                    {"field_id": "test-field", "value": "Sally"},
                ],
                "subject": "test subject",
                "block_id": "form-id",
            },
        )

        assert response.status_code == 200
        response = self.export_csv()
        data = [*csv.reader(StringIO(response.text), delimiter=",")]
        assert len(data) == 3
        # Check that 'test-field' got renamed
        assert data[0] == ["Message", "renamed-field", "date"]
        sorted_data = sorted(data[1:])
        assert sorted_data[0][:-1] == ["bye", "Sally"]
        assert sorted_data[1][:-1] == ["just want to say hi", "John"]

        # check date column. Skip seconds because can change during test
        now = datetime.now().strftime("%Y-%m-%dT%H:%M")
        assert sorted_data[0][-1].startswith(now)
        assert sorted_data[1][-1].startswith(now)
