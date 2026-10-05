from base64 import b64decode
from collective.volto.formsupport import logger
from collective.volto.formsupport.interfaces import IFormDataStore
from collective.volto.formsupport.utils import get_blocks
from copy import deepcopy
from datetime import datetime
from plone.dexterity.interfaces import IDexterityContent
from plone.namedfile import NamedBlobFile
from plone.restapi.deserializer import json_body
from repoze.catalog.catalog import Catalog
from repoze.catalog.indexes.field import CatalogFieldIndex
from repoze.catalog.query import Eq
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
        #  do not set any index here..maybe on each form
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
        soup = get_soup("form_data", self.context)
        return soup

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
                'Block with id {} and type "form" not found in context: {}.'.format(
                    self.block_id, self.context.absolute_url()
                )
            )
            return None

        fields = {
            f["field_id"]: {
                "label": f.get("custom_field_id", f.get("label", f["field_id"])),
                "type": f.get("field_type", "text"),
            }
            for f in form_fields
        }

        record = Record()
        fields_labels = {}
        fields_order = []
        fields_types = {}
        for field_data in data:
            field_id = field_data.get("field_id", "")
            value = field_data.get("value", "")
            if field_id in fields:
                field = fields[field_id]
                record.attrs[field_id] = self.storedValue(value, field["type"])
                fields_types[field_id] = field.get("type", "")
                fields_labels[field_id] = field["label"]
                fields_order.append(field_id)
            # else: skip the field
        record.attrs["fields_labels"] = fields_labels
        record.attrs["fields_order"] = fields_order
        record.attrs["fields_types"] = fields_types
        record.attrs["date"] = datetime.now()
        record.attrs["block_id"] = self.block_id
        return self.soup.add(record)

    def storedValue(self, value, type):
        if type == "attachment":
            if value:
                if value.get("encoding") == "base64":
                    data = b64decode(value["data"])
                else:
                    data = value["data"]
                return NamedBlobFile(
                    data=data,
                    filename=value.get("filename"),
                    contentType=value.get("content-type", "application/octet-stream"),
                )
        return value

    def length(self, query=None):
        return len(self.search(query=query))

    def search(self, query=None):
        """
        @param query: optional mapping with the following optional keys:
            - block_id: filter records belonging to this form block
            - start_date: only records with date >= start_date
            - end_date: only records with date <= end_date

        'block_id' is filtered through the souper/repoze.catalog index
        (it's indexed). 'date' is NOT indexed on the catalog.
        """
        query = query or {}
        block_id = query.get("block_id")
        start_date = query.get("start_date")
        end_date = query.get("end_date")

        records = self._records_by_block_id(block_id)

        if start_date or end_date:
            records = [
                record
                for record in records
                if self._matches_date_range(record, start_date, end_date)
            ]

        records.sort(key=lambda record: record.attrs.get("date"), reverse=True)
        return records

    def _records_by_block_id(self, block_id):
        """
        Return the records for the given block_id (using the catalog
        index), or every stored record if block_id is not passed.
        """
        if not block_id:
            return list(self.soup.data.values())
        _, docids = self.soup.catalog.query(Eq("block_id", block_id))
        return [self.soup.data[docid] for docid in docids]

    @staticmethod
    def _matches_date_range(record, start_date, end_date):
        """
        Whether a single record's stored 'date' attribute falls
        within [start_date, end_date]. A record with no 'date'
        attribute never matches a date-range filter.
        """
        record_date = record.attrs.get("date")
        if record_date is None:
            return False
        if start_date and record_date < start_date:
            return False
        if end_date and record_date > end_date:
            return False
        return True

    def delete(self, id):
        record = self.soup.get(id)
        del self.soup[record]

    def clear(self):
        self.soup.clear()
