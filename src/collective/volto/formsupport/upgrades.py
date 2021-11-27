# -*- coding: utf-8 -*-
from Acquisition import aq_base
from copy import deepcopy
from plone import api
from plone.dexterity.utils import iterSchemata
from zope.schema import getFields

try:
    from collective.volto.blocksfield.field import BlocksField

    HAS_BLOCKSFIELD = True
except ImportError:
    HAS_BLOCKSFIELD = False

import logging
import json

logger = logging.getLogger(__name__)

DEFAULT_PROFILE = "profile-collective.volto.formsupport:default"


def to_1100(context):  # noqa: C901
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
