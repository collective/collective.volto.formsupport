# -*- coding: utf-8 -*-
from collective.volto.formsupport.interfaces import IFormDataStore
from plone import api
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

    def show_component(self):
        if not api.user.has_permission("Modify portal content", obj=self.context):
            return False
        blocks = getattr(self.context, "blocks", {})
        if isinstance(blocks, six.text_type):
            blocks = json.loads(blocks)
        if not blocks:
            return False
        for block in blocks.values():
            if block.get("@type", "") == "form" and block.get("store", False):
                return True
        return False

    def expand_records(self, record):
        data = {k: json_compatible(v) for k, v in record.attrs.items()}
        data["id"] = record.intid
        return data


class FormDataGet(Service):
    def reply(self):
        form_data = FormData(self.context, self.request)
        return form_data(expand=True).get("form_data", {})
