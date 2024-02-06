# -*- coding: utf-8 -*-
from collective.volto.formsupport.interfaces import IFormDataStore
from plone.namedfile.utils import set_headers
from plone.namedfile.utils import stream_data
from Products.Five.browser import BrowserView
from zExceptions import NotFound
from zope.component import getMultiAdapter
from zope.interface import implementer
from zope.publisher.interfaces import IPublishTraverse


class ISavedDataTraverse(IPublishTraverse):
    pass


@implementer(ISavedDataTraverse)
class SavedData(BrowserView):
    pass


@implementer(IPublishTraverse)
class AttachmentDownload(BrowserView):
    def __init__(self, context, request):
        super().__init__(context, request)
        self.record_id = None
        self.field_id = None
        self.filename = None

    def publishTraverse(self, request, name):
        """
        e.g.
            https://nohost/page/saved_data/@@download/record_id/field_id/filename
        """
        if self.record_id is None:
            self.record_id = int(name)
        elif self.field_id is None:
            self.field_id = name
        elif self.filename is None:
            self.filename = name
        else:
            raise NotFound("Not found")
        return self

    def __call__(self):
        store = getMultiAdapter((self.context.context, self.request), IFormDataStore)
        # data = FormData(self.context, self.request)
        try:
            record = store.soup.get(self.record_id)
        except KeyError:
            raise NotFound("Record not found")
        try:
            field = record.attrs.get(self.field_id)
        except KeyError:
            raise NotFound("Field not found")
        set_headers(field, self.request.response, filename=field.filename)
        return stream_data(field)
