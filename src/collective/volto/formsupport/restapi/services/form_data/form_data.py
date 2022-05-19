# -*- coding: utf-8 -*-
from collective.volto.formsupport.interfaces import IFormDataStore
from plone import api
from plone.memoize import view
from plone.restapi.interfaces import IExpandableElement
from plone.restapi.serializer.converters import json_compatible
from plone.restapi.services import Service
from zope.component import adapter
from zope.component import getMultiAdapter
from zope.interface import implementer
from zope.interface import Interface

import json
import six


@implementer(IExpandableElement)
@adapter(Interface, Interface)
class FormData(object):
    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self, expand=False):
        if not self.show_component():
            return {}

        result = {
            "form_data": {"@id": "{}/@form-data".format(self.context.absolute_url())}
        }
        if not expand:
            return result

        store = getMultiAdapter((self.context, self.request), IFormDataStore)
        data = store.search()
        items = [self.expand_records(x) for x in data]
        data = {
            "@id": "{}/@form-data".format(self.context.absolute_url()),
            "items": items,
            "items_total": len(items),
        }

        result["form_data"] = data
        return result

    @property
    @view.memoize
    def form_block(self):
        blocks = getattr(self.context, "blocks", {})
        if isinstance(blocks, six.text_type):
            blocks = json.loads(blocks)
        if not blocks:
            return {}
        for block in blocks.values():
            if block.get("@type", "") == "form" and block.get("store", False):
                return block
        return {}

    def show_component(self):
        if not api.user.has_permission("Modify portal content", obj=self.context):
            return False
        return self.form_block and True or False

    def expand_records(self, record):
        fields_labels = record.attrs.get("fields_labels", {})
        data = {}
        for k, v in record.attrs.items():
            if k in ["fields_labels", "fields_order"]:
                continue
            data[k] = {
                "value": json_compatible(v),
                "label": fields_labels.get(k, k),
            }
        data["id"] = record.intid
        return data


class FormDataGet(Service):
    def reply(self):
        form_data = FormData(self.context, self.request)
        return form_data(expand=True).get("form_data", {})
