# -*- coding: utf-8 -*-
from zope.publisher.interfaces.browser import IDefaultBrowserLayer
from zope.interface import Interface


class ICollectiveVoltoFormsupportLayer(IDefaultBrowserLayer):
    """Marker interface that defines a browser layer."""


class IFormDataStore(Interface):
    def add(self, data):
        """
        Add data to the store

        @return: record id
        """

    def length(self):
        """
        @return: number of items stored into store
        """

    def search(self, query):
        """
        @return: items that match query
        """
