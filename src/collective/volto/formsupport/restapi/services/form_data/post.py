# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
from plone.restapi.deserializer import json_body
from plone.restapi.services import Service
from zExceptions import BadRequest
from collective.volto.formsupport.interfaces import IFormDataStore
from zope.component import getMultiAdapter
from plone.protect.interfaces import IDisableCSRFProtection
from zope.interface import alsoProvides


class FormDataDeletePost(Service):
    def reply(self):
        data = json_body(self.request)
        id = data.get("id", "")
        if not id:
            raise BadRequest("Missing record id.")
        alsoProvides(self.request, IDisableCSRFProtection)
        store = getMultiAdapter((self.context, self.request), IFormDataStore)
        try:
            store.delete(id=id)
        except KeyError:
            raise BadRequest('Record with id "{}" not found.'.format(id))

        return self.reply_no_content()
