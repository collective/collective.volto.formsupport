import copy
import json
from collections import deque

import six

from collections import deque
from hashlib import md5
from plone.keyring.interfaces import IKeyManager


def flatten_block_hierachy(blocks):
    """Given some blocks, return all contained blocks, including "subblocks"
    This allows embedding the form block into something like columns datastorage
    """

    queue = deque(list(blocks.items()))

    while queue:
        blocktuple = queue.pop()
        yield blocktuple

        block_value = blocktuple[1]

        if "data" in block_value:
            if isinstance(block_value["data"], dict):
                if "blocks" in block_value["data"]:
                    queue.extend(list(block_value["data"]["blocks"].items()))

        if "blocks" in block_value:
            queue.extend(list(block_value["blocks"].items()))


def get_blocks(context):
    """Returns all blocks from a context, including those coming from slots"""

    blocks = copy.deepcopy(getattr(context, "blocks", {}))
    if isinstance(blocks, six.text_type):
        blocks = json.loads(blocks)

    flat = list(flatten_block_hierachy(blocks))

    return dict(flat)


def generate_email_token(uid, email)
    """Generates the email verification token"""
    from zope.component import getUtility

    manager = getUtility(IKeyManager)

    return md5((uid + email + manager.secret()).encode()).hexdigest()[:10]
