from collective.volto.formsupport.interfaces import IDataAdapter
from collective.volto.formsupport.interfaces import IFormDataStore
from collective.volto.formsupport.utils import get_blocks
from datetime import datetime
from datetime import timedelta
from plone import api
from plone.memoize import view
from plone.namedfile import NamedBlobFile
from plone.protect.interfaces import IDisableCSRFProtection
from plone.restapi.batching import HypermediaBatch
from plone.restapi.interfaces import IExpandableElement
from plone.restapi.serializer.converters import json_compatible
from plone.restapi.services import Service
from zope.component import adapter
from zope.component import getAdapters
from zope.component import getMultiAdapter
from zope.interface import alsoProvides
from zope.interface import implementer
from zope.interface import Interface

import json


@implementer(IExpandableElement)
@adapter(Interface, Interface)
class FormData:
    def __init__(self, context, request, block_id=None):
        self.context = context
        self.request = request
        self.block_id = block_id or self.request.get("block_id")

    def parse_date(self, value):

        if not value:
            return None
        if isinstance(value, datetime):
            return value.replace(tzinfo=None)
        try:
            value = value.replace("Z", "+00:00")
            parsed = datetime.fromisoformat(value)
        except (ValueError, TypeError):
            return None
        return parsed.replace(tzinfo=None)

    def get_date_range(self):

        start_date = self.parse_date(self.request.get("start_date"))
        end_date = self.parse_date(self.request.get("end_date"))
        return start_date, end_date

    @view.memoize
    def get_items(self):
        block = self.form_block
        items = []
        if block:
            store = getMultiAdapter((self.context, self.request), IFormDataStore)
            remove_data_after_days = int(block.get("remove_data_after_days") or 0)

            start_date, end_date = self.get_date_range()
            query = {}
            if self.block_id:
                query["block_id"] = self.block_id
            if start_date:
                query["start_date"] = start_date
            if end_date:
                query["end_date"] = end_date

            data = store.search(query=query)

            if remove_data_after_days > 0:
                expire_date = datetime.now() - timedelta(days=remove_data_after_days)
            else:
                expire_date = None

            for record in data:
                expanded = self.expand_records(record)
                record_date = record.attrs.get("date")
                expanded["__expired"] = bool(
                    expire_date and record_date and record_date < expire_date
                )
                items.append(expanded)
        else:
            items = []
        return items

    @view.memoize
    def get_expired_items(self):
        return [item for item in self.get_items() if item["__expired"]]

    def __call__(self, expand=False):
        if not self.show_component():
            return {}
        if self.block_id:
            service_id = (
                f"{self.context.absolute_url()}/@form-data?block_id{self.block_id}"
            )
        else:
            service_id = f"{self.context.absolute_url()}/@form-data"
        result = {"form_data": {"@id": service_id}}
        if not expand:
            return result
        items = self.get_items()
        expired_total = len(self.get_expired_items())

        batch = HypermediaBatch(self.request, items)

        form_data = {
            "@id": f"{self.context.absolute_url()}/@form-data",
            "items": list(batch),
            "items_total": batch.items_total,
            "expired_total": expired_total,
        }
        if batch.links:
            form_data["batching"] = batch.links

        result["form_data"] = form_data

        adapters = getAdapters((self.context, self.request), provided=IDataAdapter)
        for _, adpt in adapters:
            result = adpt(result, block_id=self.block_id)
        return result

    @property
    @view.memoize
    def form_block(self):
        blocks = get_blocks(self.context)
        if isinstance(blocks, str):
            blocks = json.loads(blocks)
        if not blocks:
            return {}
        for id, block in blocks.items():
            if block.get("@type", "") == "form" and block.get("store", False):
                if not self.block_id or self.block_id == id:
                    return block
        return {}

    def show_component(self):
        if not api.user.has_permission("Modify portal content", obj=self.context):
            return False
        return self.form_block and True or False

    def expand_records(self, record):
        fields_labels = record.attrs.get("fields_labels", {})
        fields_types = record.attrs.get("fields_types", {})
        data = {}
        for k, v in record.attrs.items():
            if k in ["fields_labels", "fields_order", "fields_types"]:
                continue
            data[k] = {
                "field_type": fields_types.get(k, ""),
                "label": fields_labels.get(k, k),
            }
            if isinstance(v, NamedBlobFile):
                data[k]["value"] = {
                    "url": f"{self.context.absolute_url()}/saved_data/@@download/{record.intid}/{k}/{v.filename}",
                    "filename": v.filename,
                    "contentType": v.contentType,
                    "size": v.getSize(),
                }
            else:
                data[k]["value"] = json_compatible(v)
        data["id"] = record.intid
        return data


class FormDataGet(Service):
    def reply(self):

        alsoProvides(self.request, IDisableCSRFProtection)

        block_id = self.request.get("block_id")
        form_data = FormData(self.context, self.request, block_id=block_id)
        return form_data(expand=True).get("form_data", {})
