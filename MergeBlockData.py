class MergeBlockData:
    """When traversing the CFG to build the code, a DS containing MergeBlockData is passed, so that each block knows
    all control-flow constructs it is nested inside."""

    # TODO: access members through getters
    def __init__(self, merge_block, related_header):
        self.merge_block = merge_block
        self.related_header = related_header