import json
import sys
import time
import pprint
from web3 import Web3, HTTPProvider
from web3.middleware import geth_poa_middleware

RPC_URL_L2 = "https://goerli.optimism.tokamak.network"

gas_limit = 6000000

OVM_GasPriceOracle = "0x420000000000000000000000000000000000000F"
gasPriceOracleOwner = "0x8F3E9A5c4Ee4092E8CF3159dc65090CFD7e63D2e"
token_address = "0x3d15587A41851749982CDcB2880B0D3C380F84c9"

artifact_token = "MyERC20.json"
artifact_GasPriceOracle = "OVM_GasPriceOracle.json"

account = "0x757DE9c340c556b56f62eFaE859Da5e08BAAE7A2"
def get_private_key():
    return "PRIVATE_KEY"

def get_private_key_owner():
    return "PRIVATE_KEY"

def send_raw_transaction(unsigned_tx, account, gas_price, pk):
    unsigned_tx.update({"gas" : gas_limit})
    unsigned_tx.update({"gasPrice" : gas_price})
    unsigned_tx.update({"nonce" : w3.eth.getTransactionCount(account)})
    signed_tx = w3.eth.account.signTransaction(unsigned_tx, pk)
    
    tx_hash = w3.eth.sendRawTransaction(signed_tx.rawTransaction)
    print(f"tx : {tx_hash.hex()}")
    tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)
    return tx_hash, tx_receipt

def get_compiled_contract(file_path):
    with open(file_path, "r") as f:
        return json.load(f)
        
    return None   

def get_contract_instance(w3, addr, path):
    compiled = get_compiled_contract(path)
    instance = w3.eth.contract(
        address=addr,
        abi=compiled["abi"])
    return instance

w3 = Web3(HTTPProvider(RPC_URL_L2))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)

instance_GasPriceOracle = get_contract_instance(w3, OVM_GasPriceOracle, artifact_GasPriceOracle)
instance_token = get_contract_instance(w3, token_address, artifact_token)

print("#" * 60)

gas_price = instance_GasPriceOracle.functions.gasPrice().call()
print(f"gasPrice in OVM_GasPriceOracle: {gas_price}")

l1_base_fee = instance_GasPriceOracle.functions.l1BaseFee().call()
print(f"l1BaseFee in OVM_GasPriceOracle: {l1_base_fee}")

scalar = instance_GasPriceOracle.functions.scalar().call()
print(f"l1BaseFee in OVM_GasPriceOracle: {scalar}")

decimals = instance_GasPriceOracle.functions.decimals().call()
print(f"l1BaseFee in OVM_GasPriceOracle: {decimals}")

print("#" * 60)

target_address = "0x1137617aa78B50D53aE92DaB5122907F449062C4"
amount = 1
new_gas_price = int(gas_price / 2)

unsigned_tx = instance_token.functions.transfer(target_address, amount).buildTransaction({"from": account})
tx_hash, tx_receipt = send_raw_transaction(unsigned_tx, account, gas_price, get_private_key())

print(f"l1GasPrice: {tx_receipt['l1GasPrice']}")
print(f"l1GasUsed: {tx_receipt['l1GasUsed']}")
print(f"l1FeeScalar: {tx_receipt['l1FeeScalar']}")
print(f"l1Fee: {tx_receipt['l1Fee']}") # l1GasPrice * l1GasUsed * l1FeeScalar
print("#" * 60)

# should be failed to send a tx
unsigned_tx = instance_token.functions.transfer(target_address, amount).buildTransaction({"from": account})
try:
    tx_hash, tx_receipt = send_raw_transaction(unsigned_tx, account, new_gas_price, get_private_key())
    raise Exception("should not come here")
except ValueError as e:
    print(f"error: {e}")

# set new gas price
unsigned_tx = instance_GasPriceOracle.functions.setGasPrice(new_gas_price).buildTransaction({"from": gasPriceOracleOwner})
tx_hash, tx_receipt = send_raw_transaction(unsigned_tx, gasPriceOracleOwner, gas_price, get_private_key_owner())

# try again
unsigned_tx = instance_token.functions.transfer(target_address, amount).buildTransaction({"from": account})
tx_hash, tx_receipt = send_raw_transaction(unsigned_tx, account, new_gas_price, get_private_key())