from typing import Optional
import rlp
from rlp.sedes import Binary, big_endian_int, binary
import zlib

class Transaction(rlp.Serializable):
    fields = [
        ("nonce", big_endian_int),
        ("gasPrice", big_endian_int),
        ("gas", big_endian_int),
        ("to", Binary.fixed_length(20, allow_empty=True)),
        ("value", big_endian_int),
        ("input", binary),
        ("v", big_endian_int),
        ("r", big_endian_int),
        ("s", big_endian_int),
    ]

class SequencerBatchContext:
    def __init__(self, input: bytes):
        self.num_sequenced_txs = int.from_bytes(input[:6], byteorder="big")
        self.num_subsequent_queue_txs = int.from_bytes(input[6:12], byteorder="big")
        self.timestamp = int.from_bytes(input[12:22], byteorder="big")
        self.block_number = int.from_bytes(input[22:32], byteorder="big")

    def __str__(self) -> str:
        return f"num_sequenced_txs: {self.num_sequenced_txs}\n" + \
            f"num_subsequent_queue_txs: {self.num_subsequent_queue_txs}\n" + \
            f"timestamp: {self.timestamp}\n" + \
            f"block_number: {self.block_number}\n"

class SequencerBatchParams:
    def __init__(self, input: bytes):
        self.should_start_at_element = int.from_bytes(input[:5], byteorder="big")
        self.total_elements_to_append = int.from_bytes(input[5:8], byteorder="big")

        self.num_context = int.from_bytes(input[8:11], byteorder="big")
        self.contexts = []
        for i in range(self.num_context):
            self.contexts.append(SequencerBatchContext(input[11 + 16 * i : 27 + 16 * i]))

        txs_offset = 11 + 16 * self.num_context
        self.txs = []
        data_txs = zlib.decompress(input[txs_offset:])
        offset = 0
        while offset < len(data_txs):
            txs_len = int.from_bytes(data_txs[offset:offset+3], byteorder="big")
            tx = data_txs[offset+3 : offset+3+txs_len]
            
            tx_decoded = rlp.decode(tx, Transaction)
            
            self.txs.append(tx_decoded)
            offset += 3 + txs_len

    def get_num_txs(self) -> int:
        return len(self.txs)

    def get_should_start_at_element(self) -> int:
        return self.should_start_at_element

    def get_tx(self, index: int) -> Transaction:
        return self.txs[index]

    def __str__(self) -> str:
        return f"should_start_at_element: {self.should_start_at_element}\n" + \
            f"total_elements_to_append: {self.total_elements_to_append}\n" + \
            f"num_context: {self.num_context}\n"

