from collective.volto.formsupport.interfaces import IFormDataStore
from collective.volto.formsupport.utils import get_blocks
from copy import deepcopy
from io import StringIO
from plone.namedfile import NamedBlobFile
from plone.restapi.serializer.converters import json_compatible
from plone.restapi.services import Service
from zExceptions import NotFound
from zope.component import getMultiAdapter

import csv


SKIP_ATTRS = ["block_id", "fields_labels", "fields_order"]


class FormDataExportGet(Service):
    def __init__(self, context, request):
        super().__init__(context, request)
        self.form_fields_order = []
        self.form_block = None
        self.block_id = self.request.get("block_id")

        blocks = getattr(context, "blocks", {})
        if not blocks:
            raise NotFound("No blocks found")
        for block_key, block in blocks.items():
            if self.block_id and block_key != self.block_id:
                continue
            block_type = block.get("@type", "")
            if block_type == "form":
                self.form_block = block
                self.form_block_id = block_key

        if self.form_block:
            for field in self.form_block.get("subblocks", []):
                field_id = field["field_id"]
                self.form_fields_order.append(field_id)

    def get_form_fields(self):
        blocks = get_blocks(self.context)

        if not blocks:
            return {}
        form_block = {}
        for block_key, block in blocks.items():
            if block_key != self.form_block_id:
                continue
            block_type = block.get("@type", "")
            if block_type == "form":
                form_block = deepcopy(block)
        if not form_block:
            return {}

        subblocks = form_block.get("subblocks", [])

        # Restore 'custom_field_id', which is not stored with each subblock.
        for index, field in enumerate(subblocks):
            if form_block.get(field["field_id"]):
                subblocks[index]["custom_field_id"] = form_block.get(field["field_id"])

        return subblocks

    def get_ordered_keys(self, record):
        """
        Keep the form's field order, even when its schema changes over time.
        A record may contain fields that are no longer in the form.
        """
        record_order = record.attrs.get("fields_order", [])
        if record_order:
            return record_order
        order = []
        # first add the keys that are currently in the form
        for k in self.form_fields_order:
            if k in record.attrs:
                order.append(k)
        # Append stored fields that are no longer in the form.
        for k in record.attrs:
            if k not in order and k not in SKIP_ATTRS:
                order.append(k)
        return order

    def render(self):
        self.check_permission()

        self.request.response.setHeader(
            "Content-Disposition",
            f'attachment; filename="{self.__name__}.csv"',
        )
        self.request.response.setHeader("Content-Type", "text/comma-separated-values")
        data = self.get_data()
        if isinstance(data, str):
            data = data.encode("utf-8")
        self.request.response.write(data)

    def get_fields_labels(self):
        return {
            x["field_id"]: x.get("custom_field_id", x.get("label", x["field_id"]))
            for x in self.get_form_fields()
            if x.get("field_type", "") != "static_text"
        }

    def get_data(self):
        store = getMultiAdapter((self.context, self.request), IFormDataStore)
        sbuf = StringIO()
        fixed_columns = ["date"]
        columns = []
        legacy_columns = []
        rows = []
        fields_labels = self.get_fields_labels()

        for item in store.search():
            if self.block_id and item.attrs.get("block_id") != self.block_id:
                continue
            data = {}

            for k in self.get_ordered_keys(item):
                if k in SKIP_ATTRS:
                    continue

                value = item.attrs.get(k, None)
                label = {**item.attrs.get("fields_labels", {}), **fields_labels}.get(
                    k, k
                )

                if k not in self.form_fields_order and label not in legacy_columns:
                    legacy_columns.append(label)

                if isinstance(value, NamedBlobFile):
                    data[label] = value.filename
                else:
                    data[label] = json_compatible(value)

            for k in fixed_columns:
                # add fixed columns values
                value = item.attrs.get(k, None)
                data[k] = json_compatible(value)

            rows.append(data)

        columns.extend(fields_labels.values())
        columns.extend(sorted(legacy_columns))
        columns.extend(fixed_columns)

        writer = csv.DictWriter(sbuf, fieldnames=columns, quoting=csv.QUOTE_ALL)
        writer.writeheader()

        for row in rows:
            writer.writerow(row)

        res = sbuf.getvalue()
        sbuf.close()

        return res
