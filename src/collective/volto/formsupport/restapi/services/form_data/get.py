# -*- coding: utf-8 -*-
from collective.volto.formsupport import _
from collective.volto.formsupport.interfaces import IFormDataStore
from plone.protect.interfaces import IDisableCSRFProtection
from plone.restapi.serializer.converters import json_compatible
from plone.restapi.services import Service
from six import StringIO
from zExceptions import BadRequest
from zope.component import getMultiAdapter
from zope.i18n import translate
from zope.interface import alsoProvides

import csv
import six


class FormDataGet(Service):
    def reply(self):
        store = getMultiAdapter((self.context, self.request), IFormDataStore)
        data = store.search()
        items = [self.expand_records(x) for x in data]
        res = {
            "@id": "{}/@form-data".format(self.context.absolute_url()),
            "items": items,
            "items_total": len(items),
        }
        return res

    def expand_records(self, record):
        data = {k: json_compatible(v) for k, v in record.attrs.items()}
        data["id"] = record.intid
        return data


class FormDataExportGet(Service):
    def render(self):
        self.check_permission()

        self.request.response.setHeader(
            "Content-Disposition",
            'attachment; filename="{0}.csv"'.format(self.__name__),
        )
        self.request.response.setHeader(
            "Content-Type", "text/comma-separated-values"
        )

        data = self.get_data()
        if isinstance(data, six.text_type):
            data = data.encode("utf-8")
        self.request.response.write(data)

    def get_data(self):
        store = getMultiAdapter((self.context, self.request), IFormDataStore)
        if not store.block_id:
            raise BadRequest(
                translate(
                    _("missing_blockid_label", default="Missing block_id"),
                    context=self.request,
                )
            )
        form_fields = store.get_form_fields()
        if not form_fields:
            return None

        sbuf = StringIO()

        columns = form_fields["ids"] + ["date"]

        rows = []
        for item in store.search():
            data = {}
            for k, v in item.attrs.items():
                if k not in columns:
                    columns.append(k)
                data[k] = json_compatible(v)
            rows.append(data)

        writer = csv.DictWriter(sbuf, fieldnames=columns, delimiter=",")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
        res = sbuf.getvalue()
        sbuf.close()
        return res


class FormDataClear(Service):
    def reply(self):
        alsoProvides(self.request, IDisableCSRFProtection)
        store = getMultiAdapter((self.context, self.request), IFormDataStore)
        store.clear()

        return self.reply_no_content()
