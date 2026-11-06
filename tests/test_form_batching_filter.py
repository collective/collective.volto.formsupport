from collective.volto.formsupport.interfaces import IFormDataStore
from collective.volto.formsupport.testing import (
    VOLTO_FORMSUPPORT_API_FUNCTIONAL_TESTING,
)
from datetime import datetime
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import SITE_OWNER_NAME
from plone.app.testing import SITE_OWNER_PASSWORD
from plone.app.testing import TEST_USER_ID
from plone.restapi.testing import RelativeSession
from zope.component import getMultiAdapter

import transaction
import unittest


class TestFormDataBatching(unittest.TestCase):
    layer = VOLTO_FORMSUPPORT_API_FUNCTIONAL_TESTING

    def setUp(self):
        self.app = self.layer["app"]
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
        self.portal_url = self.portal.absolute_url()

        setRoles(self.portal, TEST_USER_ID, ["Manager"])

        self.api_session = RelativeSession(self.portal_url)
        self.api_session.headers.update({"Accept": "application/json"})
        self.api_session.auth = (SITE_OWNER_NAME, SITE_OWNER_PASSWORD)

        self.document = api.content.create(
            type="Document",
            title="Example context",
            container=self.portal,
        )
        self.document.blocks = {
            "form-id": {
                "@type": "form",
                "store": True,
                "subblocks": [
                    {"label": "Message", "field_id": "message", "field_type": "text"},
                    {"label": "Name", "field_id": "name", "field_type": "text"},
                ],
            },
        }
        self.document_url = self.document.absolute_url()

        transaction.commit()

    def tearDown(self):
        self.api_session.close()

    def submit_form(self, name, message):
        url = f"{self.document_url}/@submit-form"
        response = self.api_session.post(
            url,
            json={
                "from": "john@doe.com",
                "data": [
                    {"field_id": "message", "value": message},
                    {"field_id": "name", "value": name},
                ],
                "subject": "test subject",
                "block_id": "form-id",
            },
        )
        transaction.commit()
        return response

    def export_data(self, **params):
        url = f"{self.document_url}/@form-data"
        return self.api_session.get(url, params=params or None)

    def create_five_submissions_from_2026_09_01(self):
        names = ["Alice", "Bob", "Charlie", "Dave", "Erin"]
        for name in names:
            self.submit_form(name=name, message=f"message from {name}")

        store = getMultiAdapter((self.document, self.request), IFormDataStore)
        records = sorted(
            store.soup.data.values(), key=lambda record: record.attrs["date"]
        )
        self.assertEqual(len(records), 5)

        new_dates = [datetime(2026, 9, day) for day in range(1, 6)]
        for record, new_date in zip(records, new_dates, strict=True):
            record.attrs["date"] = new_date
        store.soup.reindex(records)
        transaction.commit()
        return records

    def test_batch_pagination_returns_paged_results(self):
        self.create_five_submissions_from_2026_09_01()

        response = self.export_data(b_size=2, b_start=0)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["items_total"], 5)
        self.assertEqual(len(data["items"]), 2)
        self.assertIn("batching", data)
        self.assertIn("next", data["batching"])
        self.assertNotIn("prev", data["batching"])

        response = self.export_data(b_size=2, b_start=2)
        self.assertEqual(response.status_code, 200)
        data_middle = response.json()
        self.assertEqual(data_middle["items_total"], 5)
        self.assertEqual(len(data_middle["items"]), 2)
        self.assertIn("prev", data_middle["batching"])
        self.assertIn("next", data_middle["batching"])

        response = self.export_data(b_size=2, b_start=4)
        self.assertEqual(response.status_code, 200)
        data_last = response.json()
        self.assertEqual(data_last["items_total"], 5)
        self.assertEqual(len(data_last["items"]), 1)
        self.assertIn("prev", data_last["batching"])
        self.assertNotIn("next", data_last["batching"])

        all_names = (
            [item["name"]["value"] for item in data["items"]]
            + [item["name"]["value"] for item in data_middle["items"]]
            + [item["name"]["value"] for item in data_last["items"]]
        )
        self.assertEqual(sorted(all_names), ["Alice", "Bob", "Charlie", "Dave", "Erin"])

    def test_batch_pagination_combined_with_date_filter(self):
        self.create_five_submissions_from_2026_09_01()

        response = self.export_data(
            start_date="2026-09-02",
            end_date="2026-09-04",
            b_size=2,
            b_start=0,
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["items_total"], 3)
        self.assertEqual(len(data["items"]), 2)
        self.assertIn("next", data["batching"])

        response = self.export_data(
            start_date="2026-09-02",
            end_date="2026-09-04",
            b_size=2,
            b_start=2,
        )
        self.assertEqual(response.status_code, 200)
        data2 = response.json()
        self.assertEqual(data2["items_total"], 3)
        self.assertEqual(len(data2["items"]), 1)
        self.assertNotIn("next", data2["batching"])

    def test_search_with_earlier_dates_returns_no_results(self):
        self.create_five_submissions_from_2026_09_01()

        response = self.export_data(
            start_date="2020-01-01",
            end_date="2020-12-31",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["items_total"], 0)
        self.assertEqual(data["items"], [])
