# -*- coding: utf-8 -*-
from collective.volto.formsupport.interfaces import IFormDataStore
from datetime import datetime
from datetime import timedelta
from plone import api
from zope.component import getMultiAdapter
from zope.globalrequest import getRequest

import click
import transaction


@click.command(
    help="bin/instance -OPlone run bin/formsupport_data_cleansing [--dryrun|--no-dryrun]",
    context_settings=dict(
        ignore_unknown_options=True,
    ),
)
@click.option("--dryrun", is_flag=True, default=True, help="--dryrun (default) simulate, --no-dryrun actually save the changes")
@click.option("--days", type=int, default=6 * 30, help="default number of days of data retention (default 180)")
def main(dryrun, days):
    if dryrun:
        print("CHECK ONLY")
    catalog = api.portal.get_tool("portal_catalog")
    if "blocks_type" in catalog.indexes():
        brains = catalog(block_types="form")
    else:
        print("[WARN] This script is optimized with plone.volto >= 4.1.0")
        brains = catalog()
    for brain in brains:
        obj = brain.getObject()
        blocks = getattr(obj, "blocks", None)
        if isinstance(blocks, dict):
            for block in blocks.values():
                if block.get("@type", "") != "form":
                    continue
                if not block.get("store", False):
                    continue
                if block.get("remove_data_after_days") in (-1, "-1"):
                    continue
                store = getMultiAdapter((obj, getRequest()), IFormDataStore)
                expire_date = datetime.now() - timedelta(
                    days=block.get("remove_data_after_days", days)
                )
                todelete = [
                    record.intid
                    for record in store.search()
                    if record.attrs["date"] < expire_date
                ]
                if todelete:
                    print(f"DELETE {len(todelete)} records from {brain.getPath()}")
                    for intid in todelete:
                        store.delete(intid)

    if not dryrun:
        print("COMMIT")
        transaction.commit()
