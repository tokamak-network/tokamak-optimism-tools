class CTCElementError(Exception):
    def __init__(self, element_index: int, l2_block_number: int, field: str):
        self.msg = f"CTC batch mismatch({field}). element_index: {element_index}, l2_block_number: {l2_block_number}"

    def __str__(self):
        return self.msg

class SCCElementError(Exception):
    def __init__(self, element_index: int, l2_block_number: int, field: str):
        self.msg = f"SCC batch mismatch({field}). element_index: {element_index}, l2_block_number: {l2_block_number}"

    def __str__(self):
        return self.msg