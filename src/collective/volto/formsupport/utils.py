from collections import deque


def flatten_block_hierachy(blocks):
    """ Given some blocks, return all contained blocks, including "subblocks"

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
                    queue.extend(list(
                        block_value["data"]["blocks"].items()))

        if "blocks" in block_value:
            queue.extend(list(block_value["blocks"].items()))
