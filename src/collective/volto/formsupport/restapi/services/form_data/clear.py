# -*- coding: utf-8 -*-
from collective.volto.formsupport.interfaces import IFormDataStore
from plone.protect.interfaces import IDisableCSRFProtection
from plone.restapi.services import Service
from zope.component import getMultiAdapter
from zope.interface import alsoProvides


class FormDataClear(Service):
    def reply(self):
        alsoProvides(self.request, IDisableCSRFProtection)
        store = getMultiAdapter((self.context, self.request), IFormDataStore)
        store.clear()

        return self.reply_no_content()
