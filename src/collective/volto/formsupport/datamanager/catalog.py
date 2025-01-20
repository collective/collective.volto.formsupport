from collective.volto.formsupport import logger
from collective.volto.formsupport.interfaces import IFormDataStore
from collective.volto.formsupport.utils import get_blocks
from copy import deepcopy
from datetime import datetime
from plone.dexterity.interfaces import IDexterityContent
from plone.restapi.deserializer import json_body
from repoze.catalog.catalog import Catalog
from repoze.catalog.indexes.field import CatalogFieldIndex
from souper.interfaces import ICatalogFactory
from souper.soup import get_soup
from souper.soup import NodeAttributeIndexer
from souper.soup import Record
from zope.component import adapter
from zope.interface import implementer
from zope.interface import Interface


@implementer(ICatalogFactory)
class FormDataSoupCatalogFactory:
    def __call__(self, context):
        #  do not set any index here..maybe on each form
        catalog = Catalog()
        block_id_indexer = NodeAttributeIndexer("block_id")
        catalog["block_id"] = CatalogFieldIndex(block_id_indexer)
        return catalog


@implementer(IFormDataStore)
@adapter(IDexterityContent, Interface)
class FormDataStore:
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

    def get_block(self):
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

        return form_block

    def get_form_fields(self):
        form_block = self.get_block()

        subblocks = form_block.get("subblocks", [])

        # Add the 'custom_field_id' field back in as this isn't stored with each subblock
        for index, field in enumerate(subblocks):
            if form_block.get(field["field_id"]):
                subblocks[index]["custom_field_id"] = form_block.get(field["field_id"])

        return subblocks

    def add(self, data):
        form_fields = self.get_form_fields()
        if not form_fields:
            logger.error(
                'Block with id {} and type "form" not found in context: {}.'.format(
                    self.block_id, self.context.absolute_url()
                )
            )
            return None
        fields = {}
        for field in form_fields:
            custom_field_id = field.get("custom_field_id")
            field_id = custom_field_id if custom_field_id else field["field_id"]
            fields[field_id] = field.get("label", field_id)

        record = Record()
        fields_labels = {}
        fields_order = []
        for field_data in data:
            field_id = field_data.field_id
            # TODO: not nice using the protected member to access the real internal value, but easiest way.
            value = field_data.internal_value
            if field_id in fields:
                record.attrs[field_id] = value
                fields_labels[field_id] = fields[field_id]
                fields_order.append(field_id)
        record.attrs["fields_labels"] = fields_labels
        record.attrs["fields_order"] = fields_order
        record.attrs["date"] = datetime.now()
        if self.get_block()['sendAdditionalInfo']:
            record.attrs["url"] = self.context.absolute_url_path()
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
