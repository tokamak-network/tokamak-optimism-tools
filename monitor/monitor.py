import time
from typing import Dict, List
from web3 import Web3, HTTPProvider
from web3.middleware import geth_poa_middleware

from util_contract import get_contract_instance
from sequencer_batch import SequencerBatchParams
from state_batch import StateBatchParams
from error import CTCElementError, SCCElementError

event_abi_TransactionBatchAppended = "TransactionBatchAppended(uint256,bytes32,uint256,uint256,bytes)"
event_abi_SequencerBatchAppended = "SequencerBatchAppended(uint256,uint256,uint256)"
event_abi_StateBatchAppended = "StateBatchAppended(uint256,bytes32,uint256,uint256,bytes)"

class Monitor:
    def __init__(self, rpc_url_l1: str, rpc_url_l2: str, addresses: Dict[str, str]) -> None:
        self.rpc_url_l1 = rpc_url_l1
        self.rpc_url_l2 = rpc_url_l2
        self.addresses = addresses

        self.LATEST_BLOCK_LOG_PATH = "latest_block"

        self.connect()
        self.connect_contracts_l1()
        self.init_events()

    def connect(self) -> None:
        self.w3_l1 = Web3(HTTPProvider(self.rpc_url_l1))
        self.w3_l2 = Web3(HTTPProvider(self.rpc_url_l2))
        self.w3_l2.middleware_onion.inject(geth_poa_middleware, layer=0)

    def connect_contracts_l1(self) -> None:
        for name, address in self.addresses["L1"].items():
            path = f"artifacts/{name}.json"
            if name == "ChainStorageContainer_SCC_batches" or name == "ChainStorageContainer_CTC_batches":
                path = "artifacts/ChainStorageContainer.json"

            instance = get_contract_instance(self.w3_l1, address, path)
            exec(f'self.{name} = instance')

    def init_events(self) -> None:
        self.event_hash_TransactionBatchAppended = self.w3_l1.keccak(
            text=event_abi_TransactionBatchAppended
        ).hex()
        self.event_hash_SequencerBatchAppended = self.w3_l1.keccak(
            text=event_abi_SequencerBatchAppended
        ).hex()
        self.event_hash_StateBatchAppended = self.w3_l1.keccak(
            text=event_abi_StateBatchAppended
        ).hex()

        self.monitoring_events = [[
            self.event_hash_TransactionBatchAppended,
            self.event_hash_StateBatchAppended
        ]]

        self.monitoring_addresses = [
            self.addresses["L1"]["CanonicalTransactionChain"],
            self.addresses["L1"]["StateCommitmentChain"]
        ]

    def get_from_block(self) -> int:
        from_block = self.w3_l1.eth.get_block("latest")["number"]
        try:
            with open(self.LATEST_BLOCK_LOG_PATH, "r", encoding="utf-8") as f:
                from_block = int(f.read()) + 1
        except:
            pass

        return from_block

    def save_latest_block(self, block_number: int) -> None:
        with open(self.LATEST_BLOCK_LOG_PATH, "w", encoding="utf-8") as f:
            f.write(str(block_number))

    def verify_ctc_batch(self, batch: SequencerBatchParams) -> bool:
        block_number = batch.get_should_start_at_element() + 1
        for i in range(batch.get_num_txs()):
            block = self.w3_l2.eth.get_block(block_number + i)
            tx_hash = block["transactions"][0]
            tx = self.w3_l2.eth.get_transaction(tx_hash)
            
            batch_tx = batch.get_tx(i)
            
            if batch_tx["nonce"] != tx["nonce"]:
                raise CTCElementError(block_number - 1, block_number, "nonce")
            if batch_tx["gasPrice"] != tx["gasPrice"]:
                raise CTCElementError(block_number - 1, block_number, "gasPrice")
            if batch_tx["gas"] != tx["gas"]:
                raise CTCElementError(block_number - 1, block_number, "gas")
            if self.w3_l1.toChecksumAddress(batch_tx["to"].hex()) != tx["to"]:
                raise CTCElementError(block_number - 1, block_number, "to")
            if batch_tx["value"] != tx["value"]:
                raise CTCElementError(block_number - 1, block_number, "value")
            if batch_tx["input"] != bytes.fromhex(tx["input"][2:]):
                raise CTCElementError(block_number - 1, block_number, "input")
            if batch_tx["v"] != tx["v"]:
                raise CTCElementError(block_number - 1, block_number, "v")
            if batch_tx["r"] != int.from_bytes(tx["r"], byteorder="big"):
                raise CTCElementError(block_number - 1, block_number, "r")
            if batch_tx["s"] != int.from_bytes(tx["s"], byteorder="big"):
                raise CTCElementError(block_number - 1, block_number, "s")
        
        return True

    def verify_scc_batch(self, batch: StateBatchParams) -> bool:
        block_number = batch.get_should_start_at_element() + 1
        for i in range(batch.get_num_states()):
            block = self.w3_l2.eth.get_block(block_number + i)
            l2_state = block["stateRoot"]
            batch_state = batch.get_state(i)

            if l2_state != batch_state:
                raise SCCElementError(block_number - 1, block_number, "stateRoot")
        return True

    def get_ctc_batch(self, tx_hash: str) -> SequencerBatchParams:
        tx = self.w3_l1.eth.get_transaction(tx_hash)
        return SequencerBatchParams(bytes.fromhex(tx['input'][10:]))

    def get_scc_batch(self, tx_hash: str) -> StateBatchParams:
        tx = self.w3_l1.eth.get_transaction(tx_hash)
        return StateBatchParams(bytes.fromhex(tx['input'][10:]))

    def get_events(self, from_block: int, to_block: int) -> None:
        logs = self.w3_l1.eth.get_logs({
            'fromBlock': from_block,
            'toBlock': to_block,
            'address': self.monitoring_addresses,
            'topics': self.monitoring_events
        })

        events = list({event["transactionHash"]:event for event in logs}.values())

        ctc_events = list(filter(lambda log: log["topics"][0].hex() == self.event_hash_TransactionBatchAppended, events))
        for event in ctc_events:
            batch = self.get_ctc_batch(event["transactionHash"])
            try:
                self.verify_ctc_batch(batch)
            except CTCElementError as e:
                #TODO: send error message to slack
                raise e


        scc_events = list(filter(lambda log: log["topics"][0].hex() == self.event_hash_StateBatchAppended, events))
        for event in scc_events:
            batch = self.get_scc_batch(event["transactionHash"])
            try:
                self.verify_scc_batch(batch)
            except SCCElementError as e:
                #TODO: send error message to slack
                raise e

    def loop(self) -> None:
        from_block = self.get_from_block()
        to_block = min(self.w3_l1.eth.get_block("latest")["number"], from_block + 1000)

        # wait for next block
        if to_block < from_block:
            time.sleep(60)
            return

        print(f"from_block: {from_block}, to_block: {to_block}...", end=" ")
        self.get_events(from_block, to_block)
        print("Done.")

        self.save_latest_block(to_block)