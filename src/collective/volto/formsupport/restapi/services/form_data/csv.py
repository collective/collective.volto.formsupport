from collective.volto.formsupport.interfaces import IFormDataStore
from io import StringIO
from plone.restapi.serializer.converters import json_compatible
from plone.restapi.services import Service
from zope.component import getMultiAdapter

import csv


SKIP_ATTRS = ["block_id", "fields_labels", "fields_order"]


class FormDataExportGet(Service):
    def __init__(self, context, request):
        super().__init__(context, request)
        self.form_fields_order = []
        self.form_block = {}

        blocks = getattr(context, "blocks", {})
        if not blocks:
            return
        for id, block in blocks.items():
            block_type = block.get("@type", "")
            if block_type == "form":
                self.form_block = block

        if self.form_block:
            for field in self.form_block.get("subblocks", []):
                field_id = field["field_id"]
                self.form_fields_order.append(field_id)

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

    def get_fields_labels(self, item):
        return item.attrs.get("fields_labels", {})

    def get_data(self):
        store = getMultiAdapter((self.context, self.request), IFormDataStore)
        sbuf = StringIO()
        fixed_columns = ["date"]
        columns = []

        rows = []
        for item in store.search():
            data = {}
            fields_labels = self.get_fields_labels(item)
            for k in self.form_fields_order:
                if k in SKIP_ATTRS:
                    continue
                value = item.attrs.get(k, None)
                label = fields_labels.get(k, k)
                if label not in columns and label not in fixed_columns:
                    columns.append(label)
                data[label] = json_compatible(value)
            for k in fixed_columns:
                # add fixed columns values
                value = item.attrs.get(k, None)
                data[k] = json_compatible(value)
            rows.append(data)

        columns.extend(fixed_columns)
        writer = csv.DictWriter(sbuf, fieldnames=columns, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
        res = sbuf.getvalue()
        sbuf.close()
        return res
