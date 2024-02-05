# -*- coding: utf-8 -*-
from collective.volto.formsupport.interfaces import IFormDataStore
from plone.restapi.serializer.converters import json_compatible
from plone.restapi.services import Service
from six import StringIO
from zope.component import getMultiAdapter
from zope.component import getUtility
from plone.i18n.normalizer.interfaces import IIDNormalizer
from datetime import datetime

import csv
import six

SKIP_ATTRS = ["block_id", "fields_labels", "fields_order"]


class FormDataExportGet(Service):
    def __init__(self, context, request):
        super().__init__(context, request)
        self.form_fields_order = []
        self.form_fields_labels = {}
        self.form_block = {}

        blocks = getattr(context, "blocks", {})
        if not blocks:
            return
        for block in blocks.values():
            block_type = block.get("@type", "")
            if block_type == "form":
                self.form_block = block

        if self.form_block:
            for field in self.form_block.get("subblocks", []):
                if field["field_type"] == "static_text":
                    continue
                field_id = field["field_id"]
                self.form_fields_order.append(field_id)
                # can be customized.
                # see https://github.com/collective/collective.volto.formsupport/pull/22
                self.form_fields_labels[field_id] = self.form_block.get(
                    field_id, field["label"]
                )

    def get_export_filename(self):
        title = self.form_block.get("title", "")
        filename = ""
        if not title:
            filename = "export-form"
        else:
            normalizer = getUtility(IIDNormalizer)
            filename = normalizer.normalize(title)
        now = datetime.now().strftime("%Y%m%dT%H%M")
        return f"{filename}-{now}.csv"

    def render(self):
        self.check_permission()
        self.request.response.setHeader(
            "Content-Disposition",
            f'attachment; filename="{self.get_export_filename()}"',
        )
        self.request.response.setHeader("Content-Type", "text/comma-separated-values")
        data = self.get_data()
        if isinstance(data, six.text_type):
            data = data.encode("utf-8")
        self.request.response.write(data)

    def get_data(self):
        """
        Return only data for fields in the current form setting,
        ignore old fields stored in some record
        """
        store = getMultiAdapter((self.context, self.request), IFormDataStore)
        sbuf = StringIO()
        fixed_columns = ["date"]
        columns = [self.form_fields_labels.get(k, k) for k in self.form_fields_order]
        columns.extend(fixed_columns)

        rows = []
        for item in store.search():
            data = []
            for k in self.form_fields_order:
                value = item.attrs.get(k, None)
                data.append(json_compatible(value))
            for k in fixed_columns:
                # add fixed columns values
                value = item.attrs.get(k, None)
                data.append(json_compatible(value))
            rows.append(data)
        writer = csv.writer(sbuf, quoting=csv.QUOTE_ALL)
        # header
        writer.writerow(columns)
        # data
        writer.writerows(rows)
        res = sbuf.getvalue()
        sbuf.close()
        return res
