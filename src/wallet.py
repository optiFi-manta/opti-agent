import os
import orjson
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

class AgentWallet:
    def __init__(self):
        self.file_path = "./data/wallet.json"
        MANTA_RPC_URL = Web3.HTTPProvider(os.getenv("MANTA_RPC_URL"))
        self.w3 = Web3(MANTA_RPC_URL)
        self.admin_private_key=os.getenv("PRIVATE_KEY")

    async def create_wallet(self, user_address):
        existing_data = await self._load_existing_data()
        
        for entry in existing_data:
            if entry["user_address"] == user_address:
                print(f"Wallet already exists for user address: {user_address}")
                return
        
        private_key = self.w3.eth.account.create()._private_key.hex()
        await self.save_wallet_data(private_key, user_address)
        

    async def save_wallet_data(self, private_key, user_address):
        output_data = {
            "user_address": user_address,
            "data": private_key
        }

        existing_data = await self._load_existing_data()
        existing_data.append(output_data)
        await self._save_data(existing_data)
        print("Wallet data saved successfully.")

    async def fetch_data(self, user_address):
        existing_data = await self._load_existing_data()

        for entry in existing_data:
            if entry["user_address"] == user_address:
                private_key = entry["data"]
                
                return private_key

        print(f"No wallet data found for user address: {user_address}")
        return None
    
    async def _check_address(self, user_address):
        private_key = await self.fetch_data(user_address)
        account = Web3().eth.account.from_key(private_key)
        return account.address
    
    async def _fund_wallet(self, user_address):
        private_key = await self.fetch_data(user_address)

        sender_address = self.w3.eth.account.from_key(self.admin_private_key).address
        receiver_address = self.w3.eth.account.from_key(private_key).address
        
        nonce = self.w3.eth.get_transaction_count(sender_address)
        transaction = {
            'to': receiver_address,
            'value': self.w3.to_wei(0.0001, 'ether'),
            'gas': 1000000,
            'gasPrice': self.w3.eth.gas_price,
            'nonce': nonce,
            'chainId': 3441006,
        }

        signed_txn = self.w3.eth.account.sign_transaction(transaction, self.admin_private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        self.w3.eth.wait_for_transaction_receipt(tx_hash)
        
        return f"0x{tx_hash.hex()}"

    
    async def _transfer(self, user_address, amount, asset_id, destination):
        amount = amount * 10 ** 6
        private_key = await self.fetch_data(user_address)
        sender_address = self.w3.eth.account.from_key(self.admin_private_key).address
        
        contract_address = await self._get_token_ca(asset_id)
        token_contract = self.w3.eth.contract(address=contract_address, abi=self._read_abi("abi/MockToken.json"))
    
        nonce = self.w3.eth.get_transaction_count(sender_address)
        
        transaction = token_contract.functions.transfer(destination, amount).build_transaction({
            'nonce': nonce,
            'gas': 1000000,
            'gasPrice': self.w3.eth.gas_price,
            'chainId': 3441006,
        })

        signed_txn = self.w3.eth.account.sign_transaction(transaction, private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        self.w3.eth.wait_for_transaction_receipt(tx_hash)
        
        return f"0x{tx_hash.hex()}"
    
    async def _get_token_ca(self, asset_id):
        match asset_id:
            case "usdc":
                return "0x94F0Fd09f425Be15C7Bc0575Aa71780A044039e3"
            case "uni":
                return "0x6c8D1fd3AA9F436CBA20E4b6A5aeDb1bf814A732"
            case "weth":
                return "0x3455b6B22cBD998512286428De8844CBFBcc06C2"
            case "usdt":
                return "0x7598099fFC36dCC3e96F3aB33f18E86F85ae7E44"
            case "dai":
                return "0x74A8Ee760959AF0B18307861e92769CfEcC42f9B"
    
    async def _get_protocol_ca(self, protocol):
        match protocol:
            case "uniswap":
                return "0xa976c4930e253CE56Ff129404a95F0578345C113"
            case "compoundv3":
                return "0xd39ef51d10FAeE75FE6fe66537F3D8128Ec72dA5"
            case "usdxmoney":
                return "0xF50c64a2C422C6809e5BdbcF4Bb5af38D06a033a"
            case "stargatev3":
                return "0x60e78201ac487E5C382379dc8f9e39a896396728"
            case "aavev3":
                return "0x23218e77D017AD293496976A5ee9Eb3F3F5EF217"
    
    async def mint(self, user_address, asset_id, amount):
        amount = int(amount) * (10 ** 6)
        abi = await self._read_abi("./abi/MockToken.json")
        
        private_key = await self.fetch_data(user_address)
        sender_address = self.w3.eth.account.from_key(private_key).address
        
        contract_address = await self._get_token_ca(asset_id)
        token_contract = self.w3.eth.contract(address=contract_address, abi=abi)
        nonce = self.w3.eth.get_transaction_count(sender_address)
        
        transaction = token_contract.functions.mint(sender_address, amount).build_transaction({
            'chainId': 3441006,
            'gas': 1000000,
            'gasPrice': self.w3.eth.gas_price,
            'nonce': nonce,
        })
        
        signed_txn = self.w3.eth.account.sign_transaction(transaction, private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        self.w3.eth.wait_for_transaction_receipt(tx_hash)
        
        return f"0x{tx_hash.hex()}"
    
    async def transfer(self, user_address, contract_address, to, amount):
        amount = int(amount) * (10 ** 6)
        abi = await self._read_abi("./abi/MockToken.json")
        
        private_key = await self.fetch_data(user_address)
        sender_address = self.w3.eth.account.from_key(private_key).address
        
        token_contract = self.w3.eth.contract(address=contract_address, abi=abi)
        nonce = self.w3.eth.get_transaction_count(sender_address)
        
        transaction = token_contract.functions.transfer(to, amount).build_transaction({
            'chainId': 3441006,
            'gas': 1000000,
            'gasPrice': self.w3.eth.gas_price,
            'nonce': nonce,
        })
        
        signed_txn = self.w3.eth.account.sign_transaction(transaction, private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        self.w3.eth.wait_for_transaction_receipt(tx_hash)
        
        return f"0x{tx_hash.hex()}"
    
    async def swap(self, user_address, spender, token_in, token_out, amount):
        private_key = await self.fetch_data(user_address)
        sender_address = self.w3.eth.account.from_key(private_key).address
        
        amount_generalized = int(amount) * (10 ** 6)
        
        status = await self.approve(sender_address, private_key, spender, token_in, amount)
        if status:
            abi = await self._read_abi("./abi/OptiFinance.json")
            
            staking_contract = self.w3.eth.contract(address="0x0b561A287588675AccE2f190FFa2AdCb30145e01", abi=abi)
            nonce = self.w3.eth.get_transaction_count(sender_address)
            
            transaction = staking_contract.functions.swap(token_in, token_out, amount_generalized).build_transaction({
                'chainId': 3441006,
                'gas': 1000000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': nonce,
            })
            
            signed_txn = self.w3.eth.account.sign_transaction(transaction, private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
            self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            return f"0x{tx_hash.hex()}"
        else:
            return f"Error during transaction"
    
    async def approve(self, sender_address, private_key, spender, token_in, amount):
        try:
            approve_abi = await self._read_abi("./abi/MockToken.json")
            amount = int(amount) * (10 ** 6)
            
            token_contract = self.w3.eth.contract(address=token_in, abi=approve_abi)
            nonce = self.w3.eth.get_transaction_count(sender_address)
            
            transaction = token_contract.functions.approve(spender, amount+10).build_transaction({
                'chainId': 3441006,
                'gas': 1000000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': nonce,
            })
            
            signed_txn = self.w3.eth.account.sign_transaction(transaction, private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
            self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            return True
        
        except Exception as e:
            return False
    
    async def stake(self, user_address, asset_id, protocol, spender, amount):
        approve_abi = await self._read_abi("./abi/MockToken.json")
        amount = int(amount) * (10 ** 6)
        
        private_key = await self.fetch_data(user_address)
        sender_address = self.w3.eth.account.from_key(private_key).address
        
        contract_address = await self._get_token_ca(asset_id)
        token_contract = self.w3.eth.contract(address=contract_address, abi=approve_abi)
        nonce = self.w3.eth.get_transaction_count(sender_address)
        
        transaction = token_contract.functions.approve(spender, amount+10).build_transaction({
            'chainId': 3441006,
            'gas': 1000000,
            'gasPrice': self.w3.eth.gas_price,
            'nonce': nonce,
        })
        
        signed_txn = self.w3.eth.account.sign_transaction(transaction, private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        self.w3.eth.wait_for_transaction_receipt(tx_hash)
        
        #=========================================================
        
        abi = await self._read_abi("./abi/MockStake.json")
        
        contract_address = await self._get_protocol_ca(protocol)
        token_contract = self.w3.eth.contract(address=contract_address, abi=abi)
        nonce = self.w3.eth.get_transaction_count(sender_address)
        
        transaction = token_contract.functions.stake(0, amount).build_transaction({
            'chainId': 3441006,
            'gas': 1000000,
            'gasPrice': self.w3.eth.gas_price,
            'nonce': nonce,
        })
        signed_txn = self.w3.eth.account.sign_transaction(transaction, private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        self.w3.eth.wait_for_transaction_receipt(tx_hash)
        
        return f"0x{tx_hash.hex()}"
    
    
    async def unstake(self, user_address, protocol):        
        abi = await self._read_abi("./abi/MockStake.json")
        
        private_key = await self.fetch_data(user_address)
        sender_address = self.w3.eth.account.from_key(private_key).address
        
        contract_address = await self._get_protocol_ca(protocol)
        token_contract = self.w3.eth.contract(address=contract_address, abi=abi)
        nonce = self.w3.eth.get_transaction_count(sender_address)
        
        transaction = token_contract.functions.withdrawAll().build_transaction({
            'chainId': 3441006,
            'gas': 1000000,
            'gasPrice': self.w3.eth.gas_price,
            'nonce': nonce,
        })
        signed_txn = self.w3.eth.account.sign_transaction(transaction, private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        self.w3.eth.wait_for_transaction_receipt(tx_hash)
        
        return f"0x{tx_hash.hex()}"


    async def _read_abi(self, abi_path):
        with open(abi_path, 'r') as file:
            return orjson.loads(file.read())


    async def _load_existing_data(self):
        if not os.path.exists(self.file_path):
            return []

        with open(self.file_path, 'rb') as file:
            return orjson.loads(file.read())

    async def _save_data(self, data):
        with open(self.file_path, 'wb') as file:
            file.write(orjson.dumps(data, option=orjson.OPT_INDENT_2))
