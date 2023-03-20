import json

def get_compiled_contract(file_path: str):
    with open(file_path, "r") as f:
        return json.load(f)
        
    return None   

def get_contract_instance(w3, addr, path):
    compiled = get_compiled_contract(path)
    instance = w3.eth.contract(
        address=addr,
        abi=compiled["abi"])
    return instance