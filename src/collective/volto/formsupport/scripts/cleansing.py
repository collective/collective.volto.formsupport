from collective.volto.formsupport.interfaces import IFormDataStore
from collective.volto.formsupport.restapi.services.form_data.form_data import FormData
from plone import api
from zope.component import getMultiAdapter
from zope.globalrequest import getRequest

import click
import sys
import transaction


@click.command(
    help=(
        "bin/instance -OPlone run bin/formsupport_data_cleansing [--dryrun|--no-dryrun]"
    ),
    context_settings={"ignore_unknown_options": True, "allow_extra_args": True},
)
@click.option(
    "--dryrun/--no-dryrun",
    is_flag=True,
    default=True,
    help="--dryrun (default) simulate, --no-dryrun actually save the changes",
)
def _clean_form_block(obj, request, content_path, block_id, block):
    if block.get("@type", "") != "form" or not block.get("store", False):
        return
    remove_data_after_days = int(block.get("remove_data_after_days") or 0)
    # 0/None -> default value; -1 -> don't remove
    if remove_data_after_days <= 0:
        print(f"SKIP record cleanup from {content_path} block: {block_id}")
        return
    data = FormData(obj, request, block_id)
    store = getMultiAdapter((obj, request), IFormDataStore)
    expired_items = data.get_expired_items()
    for item in expired_items:
        store.delete(item["id"])
    if expired_items:
        print(
            f"[INFO] removed {len(expired_items)} records from {content_path} "
            f"block: {block_id}"
        )


def main(dryrun):
    if dryrun:
        print("CHECK ONLY")
    catalog = api.portal.get_tool("portal_catalog")
    root_path = "/".join(api.portal.get().getPhysicalPath())
    request = getRequest()
    if "blocks_type" in catalog.indexes():
        brains = catalog.unrestrictedSearchResults(block_types="form", path=root_path)
    else:
        print("[WARN] This script is optimized for plone.volto >= 4.1.0")
        brains = catalog.unrestrictedSearchResults(path=root_path)
    for brain in brains:
        obj = brain.getObject()
        blocks = getattr(obj, "blocks", None)
        if isinstance(blocks, dict):
            for block_id, block in blocks.items():
                _clean_form_block(obj, request, brain.getPath(), block_id, block)
    if not dryrun:
        print("COMMIT")
        transaction.commit()


if __name__ == "__main__":
    sys.exit(main())
