import asyncio
import time
from abc import ABC, abstractmethod
import os
import requests
from dotenv import load_dotenv

from main import session

load_dotenv()

class BlockchainAPI(ABC):
    """
    Абстрактный класс для взаимодействия с различными блокчейнами.
    """

    @abstractmethod
    def get_last_transactions(self, wallet_address, limit=3):
        pass

    @abstractmethod
    def get_transaction_details(self, tx_hash):
        pass


class SolanaAPI(BlockchainAPI):
    def __init__(self, rpc_url):
        self.rpc_url = rpc_url

    def get_last_transactions(self, wallet_address, limit=3):
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getSignaturesForAddress",
            "params": [wallet_address, {"limit": limit}],
        }
        response = requests.post(self.rpc_url, json=payload)
        response.raise_for_status()
        return response.json().get("result", [])

    def get_transaction_details(self, tx_hash):
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getTransaction",
            "params": [tx_hash, "jsonParsed"],
        }
        response = requests.post(self.rpc_url, json=payload)
        response.raise_for_status()
        return response.json().get("result", {})


class BinanceSmartChainAPI(BlockchainAPI):
    def __init__(self, api_key):
        self.api_key = api_key
        self.api_url = "https://api.bscscan.com/api"

    def get_last_transactions(self, wallet_address, limit=3):
        url = f"{self.api_url}?module=account&action=txlist&address={wallet_address}&apikey={self.api_key}"
        response = requests.get(url)
        response.raise_for_status()
        return response.json().get("result", [])[:limit]

    def get_last_token_transactions(self, wallet_address, contract_address, limit=3):
        url = (
            f"{self.api_url}?module=account&action=tokentx"
            f"&contractaddress={contract_address}&address={wallet_address}"
            f"&apikey={self.api_key}&sort=desc&page=1&offset={limit}"
        )
        response = requests.get(url)
        response.raise_for_status()
        return response.json().get("result", [])

    def get_transaction_details(self, tx_hash):
        return {"tx_hash": tx_hash}


class BaseApi(BlockchainAPI):
    def __init__(self, api_key):
        self.api_key = api_key
        self.api_url = "https://api.basescan.org/api"

    def get_last_transactions(self, wallet_address, limit=3):
        url = f"{self.api_url}?module=account&action=txlist&address={wallet_address}&apikey={self.api_key}"
        response = requests.get(url)
        response.raise_for_status()
        return response.json().get("result", [])[:limit]

    def get_last_token_transactions(self, wallet_address, contract_address, limit=3):
        url = (
            f"{self.api_url}?module=account&action=tokentx"
            f"&contractaddress={contract_address}&address={wallet_address}"
            f"&apikey={self.api_key}&sort=desc&page=1&offset={limit}"
        )
        response = requests.get(url)
        response.raise_for_status()
        return response.json().get("result", [])

    def get_transaction_details(self, tx_hash):
        return {"tx_hash": tx_hash}

class TronAPI(BlockchainAPI):
    def __init__(self, api_key):
        self.api_key = api_key


    def get_last_transactions(self, wallet_address, limit=3):
        url = f"https://apilist.tronscan.org/api/transaction?address={wallet_address}&limit={limit}&apikey={self.api_key}"
        response = requests.get(url)
        response.raise_for_status()
        return response.json().get("data", [])

    def get_last_token_transactions(self, wallet_address, contract_address, limit=3):
        url = (
            f"https://apilist.tronscanapi.com/api/token_trc20/transfers?module=account&action=tokentx"
            f"&contractaddress={contract_address}&address={wallet_address}"
            f"&apikey={self.api_key}&sort=desc&page=1&offset={limit}"
        )
        response = requests.get(url)
        response.raise_for_status()
        return response.json().get("data", [])

    def get_transaction_details(self, tx_hash):
        url = f"https://apilist.tronscan.org/api/transaction-info?hash={tx_hash}"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()


class TonAPI(BlockchainAPI):
    def __init__(self, api_key):
        self.api_key = api_key
        self.api_url = "https://toncenter.com/api/v2"

    def get_last_transactions(self, wallet_address, limit=3):
        params = {
            "address": wallet_address,
            "limit": limit,
            "api_key": self.api_key,
        }
        url = f"{self.api_url}/getTransactions"
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json().get("result", [])

    def get_transaction_details(self, tx_hash):
        params = {
            "hash": tx_hash,
            "api_key": self.api_key,
        }
        url = f"{self.api_url}/getTransaction"
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json().get("result", {})


class BlockchainFactory:
    """
    Фабрика для создания объектов API блокчейнов.
    """
    @staticmethod
    def get_blockchain_api(blockchain):
        if blockchain == "SOL":
            return SolanaAPI(rpc_url="https://api.mainnet-beta.solana.com")
        elif blockchain == "BSC":
            return BinanceSmartChainAPI(api_key=os.getenv("BSC_API_KEY"))
        elif blockchain == "TRON":
            return TronAPI(api_key=os.getenv("TRON_API_KEY"))
        elif blockchain == "TON":
            return TonAPI(api_key=os.getenv("TON_API_KEY"))
        elif blockchain == "BASE":
            return BaseApi(api_key=os.getenv("BASE_API_KEY"))
        else:
            raise ValueError(f"Блокчейн {blockchain} не поддерживается.")


def is_transaction_valid(received_amount, expected_amount, tolerance=0.0001):
    """
    Проверяет, попадает ли сумма в допустимый диапазон.
    """
    return abs(received_amount - expected_amount) <= (expected_amount * tolerance)


def check_payment(wallet_address, blockchain, expected_amount, token_contract=None, tolerance=0.0001):
    """
    Универсальная проверка транзакций.
    """
    blockchain_api = BlockchainFactory.get_blockchain_api(blockchain)
    if token_contract:
        transactions = blockchain_api.get_last_token_transactions(wallet_address, token_contract)
        print(transactions)
        #TODO закончить трон юсдт
        for tx in transactions:
            print(tx)
            amount = float(tx.get("value")) / 1e18
            tx_hash = tx.get("hash")
            if is_transaction_valid(amount, expected_amount, tolerance):
                return True, tx_hash

    transactions = blockchain_api.get_last_transactions(wallet_address)
    amount = 0
    count = 10
    tx_hash = None
    for tx in transactions:
        count += 1
        # Извлечение деталей транзакции
        if blockchain == "TON":
            amount = float(tx.get("in_msg", {}).get("value", 0)) / 1e9  # TON -> Decimal
            tx_hash = tx.get("transaction_id").get("hash")
        elif blockchain == "SOL":
            time.sleep(1)
            details = blockchain_api.get_transaction_details(tx.get("signature"))
            instructions = details.get("transaction", {}).get("message", {}).get("instructions", [])
            for instruction in instructions:
                if instruction.get("programId") == "11111111111111111111111111111111" and instruction.get("parsed", {}).get("info", {}).get("destination", "") == os.environ.get("SOL_WALLET_ADDRESS"):
                    amount = float(instruction.get("parsed", {}).get("info", {}).get("lamports", 0)) / 1e9
                    tx_hash = tx.get("signature")
                    if count > 3:
                        break
        elif blockchain == "BSC" or blockchain == "BASE":
            amount = float(tx.get("value", 0)) / 1e18
            tx_hash = tx.get("hash")
        elif blockchain == "TRON":
            amount = float(tx.get("contractData").get("amount", 0)) / 1e6
            tx_hash = tx.get("hash")

        if is_transaction_valid(amount, expected_amount, tolerance):
            return True, tx_hash

    return False, None

print(check_payment(wallet_address="TXtqa1XH8DKfofYWZH6R4DvRekmC2WfZbM", blockchain="TRON", token_contract=os.environ.get("USDT_TRON_MINT_ADDRESS"), expected_amount=1.01, tolerance=0.0001))


def validate_payment(transaction):
    """
    Проверка оплаты для переданной транзакции.
    """
    token_contract = None
    if transaction.currency == "USDT" and transaction.blockchain == "Binance":
        token_contract = os.getenv("USDT_BSC_MINT_ADDRESS")
    elif transaction.currency == "USDT" and transaction.blockchain == "TRON":
        token_contract = os.getenv("USDT_TRON_MINT_ADDRESS")
    elif transaction.currency == "USDC" and transaction.blockchain == "Base":
        token_contract = os.getenv("USDC_BASE_MINT_ADDRESS")

    is_valid, tx_id = check_payment(
        wallet_address=transaction.wallet_address,
        blockchain=transaction.blockchain,
        expected_amount=transaction.expected_amount,
        token_contract=token_contract,
    )

    if is_valid:
        transaction.status = "Success"
        transaction.tx_id = tx_id
        session.commit()
        return "Платеж подтвержден!"
    else:
        return "Оплата не найдена или сумма неверна."
