import copy
import json
from collections import deque

import six
import pyotp
import base64

from collections import deque

EMAIL_OTP_LIFETIME = 5 * 60


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


def generate_email_token(uid="", email=""):
    """Generates the email verification token"""

    totp = pyotp.TOTP(base64.b32encode((uid + email).encode()))

    return totp.now()


def validate_email_token(uid="", email="", token=""):

    totp = pyotp.TOTP(base64.b32encode((uid + email).encode()))

    return totp.verify(token, valid_window=EMAIL_OTP_LIFETIME)
