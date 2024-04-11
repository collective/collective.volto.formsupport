# -*- coding: utf-8 -*-
from Products.Five.browser import BrowserView
from plone import api


class EmailConfirmView(BrowserView):
    def __call__(self, token="alksdjfakls", *args, **kwargs):
        self.token = token

        return super().__call__(*args, **kwargs)

    def get_token(self):
        return self.token

    def get_portal(self):
        return api.portal.get()
