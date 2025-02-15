import os
import orjson
import requests
from web3 import Web3
from src.utils import get_env_variable
from dotenv import load_dotenv

load_dotenv()

def _load_existing_data(self):
    if not os.path.exists('./data/wallet.json'):
        return []

    with open('./data/wallet.json', 'rb') as file:
        return orjson.loads(file.read())
    
def fetch_data(user_address):
    existing_data = _load_existing_data()

    for entry in existing_data:
        if entry["user_address"] == user_address:
            private_key = entry["data"]
            
            return private_key

    print(f"No wallet data found for user address: {user_address}")
    return None   

def get_data_staked(user_address):
    wallet = fetch_data(user_address)
    address = wallet.default_address.address_id
    
    MANTA_RPC_URL = Web3.HTTPProvider(os.getenv("MANTA_RPC_URL"))
    w3 = Web3(Web3.HTTPProvider(MANTA_RPC_URL))

    result = requests.get("https://opti-backend.vercel.app/staking")
    response = result.json()
    address_protocol = [item['addressStaking'] for item in response]


    with open("abi/MockStake.json", 'r') as file:
        contract_abi = orjson.loads(file.read())
    
    result_amount = []
    for i in range(len(address_protocol)):
        contract_address = address_protocol[i]
        contract = w3.eth.contract(address=contract_address, abi=contract_abi)
        try:
            w3.to_checksum_address(address)
            balance = contract.functions.getAmountStakeByUser(address).call()
            readable_balance = balance / (10 ** 6)
            if int(readable_balance) > 0:
                user_staked = {
                    "protocol": contract_address,
                    "amount": readable_balance, 
                }
                result_amount.append(user_staked)
                
        except Exception as e:
            print(f"Error retrieving balance: {e}")
    
    return result_amount

def get_risk(user_address):
    wallet_data = _load_existing_data()
    for entry in wallet_data:
        if entry["user_address"] == user_address:
            return entry["risk_profile"]