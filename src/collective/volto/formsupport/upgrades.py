# -*- coding: utf-8 -*-
from Acquisition import aq_base
from copy import deepcopy
from plone import api
from plone.dexterity.utils import iterSchemata
from zope.schema import getFields
from collective.volto.formsupport.interfaces import IFormDataStore
from zope.component import getMultiAdapter
from zope.globalrequest import getRequest
from souper.soup import Record
from zope.component import getUtility
from plone.i18n.normalizer.interfaces import IIDNormalizer


try:
    from collective.volto.blocksfield.field import BlocksField

    HAS_BLOCKSFIELD = True
except ImportError:
    HAS_BLOCKSFIELD = False

from collective.volto.formsupport import logger

import json


DEFAULT_PROFILE = "profile-collective.volto.formsupport:default"


def to_1100(context):  # noqa: C901 # pragma: no cover
    logger.info("### START CONVERSION FORM BLOCKS ###")

    def fix_block(blocks, url):
        for block in blocks.values():
            if block.get("@type", "") != "form":
                continue
            found = False
            for field in block.get("subblocks", []):
                if field.get("field_type", "") == "checkbox":
                    field["field_type"] = "multiple_choice"
                    found = True
                if field.get("field_type", "") == "radio":
                    field["field_type"] = "simple_choice"
                    found = True
            if found:
                logger.info("[CONVERTED] - {}".format(url))

    # fix root
    portal = api.portal.get()
    portal_blocks = getattr(portal, "blocks", "")
    if portal_blocks:
        blocks = json.loads(portal_blocks)
        fix_block(blocks, portal.absolute_url())
        portal.blocks = json.dumps(blocks)

    # fix blocks in contents
    pc = api.portal.get_tool(name="portal_catalog")
    brains = pc()
    tot = len(brains)
    i = 0
    for brain in brains:
        i += 1
        if i % 1000 == 0:
            logger.info("Progress: {}/{}".format(i, tot))
        item = aq_base(brain.getObject())
        for schema in iterSchemata(item):
            for name, field in getFields(schema).items():
                if name == "blocks":
                    blocks = deepcopy(item.blocks)
                    if blocks:
                        fix_block(blocks, brain.getURL())
                        item.blocks = blocks
                elif HAS_BLOCKSFIELD and isinstance(field, BlocksField):
                    value = deepcopy(field.get(item))
                    if not value:
                        continue
                    if isinstance(value, str):
                        if value == "":
                            setattr(
                                item,
                                name,
                                {"blocks": {}, "blocks_layout": {"items": []}},
                            )
                            continue
                    if blocks:
                        fix_block(blocks, brain.getURL())
                        setattr(item, name, value)


def to_1200(context):  # noqa: C901 # pragma: no cover
    logger.info("### START CONVERSION STORED DATA ###")

    def get_field_info_from_block(block, field_id):
        normalizer = getUtility(IIDNormalizer)
        for field in block.get("subblocks", []):
            normalized_label = normalizer.normalize(field.get("label", ""))
            if field_id == normalized_label:
                return {"id": field["field_id"], "label": field.get("label", "")}
            elif field_id == field["field_id"]:
                return {"id": field["field_id"], "label": field.get("label", "")}
        return {"id": field_id, "label": field_id}

    def fix_data(blocks, context):
        fixed = False
        for block in blocks.values():
            if block.get("@type", "") != "form":
                continue
            if not block.get("store", False):
                continue
            store = getMultiAdapter((context, getRequest()), IFormDataStore)
            fixed = True
            data = store.search()
            for record in data:
                labels = {}
                new_record = Record()
                for k, v in record.attrs.items():
                    new_id = get_field_info_from_block(block=block, field_id=k)
                    new_record.attrs[new_id["id"]] = v
                    labels.update({new_id["id"]: new_id["label"]})
                new_record.attrs["fields_labels"] = labels
                # create new entry
                store.soup.add(new_record)
                # remove old one
                store.delete(record.intid)
        return fixed

    fixed_contents = []
    # fix root
    portal = api.portal.get()
    portal_blocks = getattr(portal, "blocks", "")
    if portal_blocks:
        blocks = json.loads(portal_blocks)
        res = fix_data(blocks, portal)
        if res:
            fixed_contents.append("/")

    # fix blocks in contents
    pc = api.portal.get_tool(name="portal_catalog")
    brains = pc()
    tot = len(brains)
    i = 0
    for brain in brains:
        i += 1
        if i % 100 == 0:
            logger.info("Progress: {}/{}".format(i, tot))
        item = brain.getObject()
        for schema in iterSchemata(item.aq_base):
            for name, field in getFields(schema).items():
                if name == "blocks":
                    blocks = getattr(item, "blocks", {})
                    if blocks:
                        res = fix_data(blocks, item)
                        if res:
                            fixed_contents.append(brain.getPath())
                elif HAS_BLOCKSFIELD and isinstance(field, BlocksField):
                    value = field.get(item)
                    if not value:
                        continue
                    if isinstance(value, str):
                        continue
                    blocks = value.get("blocks", {})
                    if blocks:
                        res = fix_data(blocks, item)
                        if res:
                            fixed_contents.append(brain.getPath())
    logger.info("Fixed {} contents:".format(len(fixed_contents)))
    for path in fixed_contents:
        logger.info("- {}".format(path))
