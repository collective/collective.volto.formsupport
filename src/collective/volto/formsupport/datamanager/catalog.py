# -*- coding: utf-8 -*-

from collective.volto.formsupport.interfaces import IFormDataStore
from collective.volto.formsupport.utils import get_blocks
from copy import deepcopy
from datetime import datetime
from plone.dexterity.interfaces import IDexterityContent
from plone.i18n.normalizer.interfaces import IIDNormalizer
from plone.restapi.deserializer import json_body
from plone.restapi.slots.interfaces import ISlot
from Products.CMFPlone.interfaces.siteroot import IPloneSiteRoot
from repoze.catalog.catalog import Catalog
from repoze.catalog.indexes.field import CatalogFieldIndex
from souper.interfaces import ICatalogFactory
from souper.soup import get_soup, NodeAttributeIndexer, Record
from zope.component import adapter, getUtility
from zope.interface import implementer, Interface

import logging


logger = logging.getLogger(__name__)


@implementer(ICatalogFactory)
class FormDataSoupCatalogFactory(object):
    def __call__(self, context):
        #  do not set any index here..maybe on each form
        catalog = Catalog()
        block_id_indexer = NodeAttributeIndexer("block_id")
        catalog[u"block_id"] = CatalogFieldIndex(block_id_indexer)
        return catalog


@implementer(IFormDataStore)
@adapter(IDexterityContent, Interface)
class FormDataStore(object):
    def __init__(self, context, request):
        self.context = context
        self.request = request

    @property
    def soup(self):
        return get_soup("form_data", self.context)

    @property
    def block_id(self):
        data = json_body(self.request)
        if not data:
            data = self.request.form
        return data.get("block_id", "")

    def get_form_fields(self):
        blocks = get_blocks(self.context)

        if not blocks:
            return {}

        form_block = {}
        for id, block in blocks.items():
            if id != self.block_id:
                continue
            block_type = block.get("@type", "")
            if block_type == "form":
                form_block = deepcopy(block)
        if not form_block:
            return {}
        return form_block.get("subblocks", [])

    def add(self, data):
        form_fields = self.get_form_fields()
        if not form_fields:
            logger.error(
                'Block with id {} and type "form" not found in context: {}.'.format(
                    self.block_id, self.context.absolute_url()
                )
            )
            return None

        form_ids = [x.get("field_id", "") for x in form_fields]
        record = Record()
        # record.attrs["metadata"] = {}
        normalizer = getUtility(IIDNormalizer)
        for field in data:
            field_id = field.get("field_id", "")
            id = normalizer.normalize(field.get("label", ""))
            value = field.get("value", "")
            if field_id in form_ids:
                record.attrs[id] = value
                # record.attrs["metadata"][id] = {
                #     "field_id": field_id,
                #     "label": field.get("label", ""),
                # }
        record.attrs["date"] = datetime.now()
        record.attrs["block_id"] = self.block_id
        return self.soup.add(record)

    def length(self):
        return len([x for x in self.soup.data.values()])

    def search(self, query=None):
        if not query:
            records = sorted(
                self.soup.data.values(),
                key=lambda k: k.attrs.get("date", ""),
                reverse=True,
            )
        return records

    def delete(self, id):
        record = self.soup.get(id)
        del self.soup[record]

    def clear(self):
        self.soup.clear()


@implementer(IFormDataStore)
@adapter(IPloneSiteRoot, Interface)
class PloneSiteFormDataStore(FormDataStore):
    def get_form_fields(self):
        # TODO: should this be getProperty?
        blocks = get_blocks(self.context)

        if not blocks:
            return {}

        form_block = {}

        for id, block in blocks.items():
            if id != self.block_id:
                continue
            block_type = block.get("@type", "")
            if block_type == "form":
                form_block = deepcopy(block)

        if not form_block:
            return {}

        return form_block.get("subblocks", [])


@implementer(IFormDataStore)
@adapter(ISlot, Interface)
class SlotDataStore(FormDataStore):
    def get_form_fields(self):
        # TODO: should this be getProperty?
        blocks = get_blocks(self.context)

        if not blocks:
            return {}

        form_block = {}

        for id, block in blocks.items():
            if id != self.block_id:
                continue
            block_type = block.get("@type", "")
            if block_type == "form":
                form_block = deepcopy(block)

        if not form_block:
            return {}

        return form_block.get("subblocks", [])
