import sys
from typing import List
from monitor import Monitor

RPC_URL_L2 = "https://goerli.optimism.tokamak.network"
ADDRESSES_L1 = {
    "ChainStorageContainer_SCC_batches": "0xdEc2F522035581d7d8a527865174E545073A5f4A",
    "StateCommitmentChain": "0xd52E839b21cE302B15f7652Dc44Cb33841450418",
    "ChainStorageContainer_CTC_batches": "0x9dDBa463f716b328fa35e8bDdDE9C27DECce18c5",
    "CanonicalTransactionChain": "0x1D288952363B14B6BEEFA6A5fB2990203963F399",
}


def main(argv: List[str]):
    if len(argv) != 1:
        print("insert L1 rpc endpoint")
        exit()

    RPC_URL_L1 = argv[0]

    monitor = Monitor(RPC_URL_L1, RPC_URL_L2, {
        "L1": ADDRESSES_L1
    })

    while True:
        monitor.loop()


if __name__ == "__main__":
    main(sys.argv[1:])