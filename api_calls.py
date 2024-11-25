import asyncio
import time
from abc import ABC, abstractmethod
import os
import requests
from dotenv import load_dotenv
from requests import HTTPError

from main import session

load_dotenv()

import requests
import os
from dotenv import load_dotenv

load_dotenv()
sol_wallet_address = os.environ.get('SOL_WALLET_ADDRESS')
bsc_wallet_address = os.environ.get('BSC_WALLET_ADDRESS')
ton_wallet_address = os.environ.get("TON_WALLET_ADDRESS")
tron_wallet_address = os.environ.get('TRON_WALLET_ADDRESS')


def get_sol_usd_rate():
    response = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=solana&vs_currencies=usd")
    if response.status_code == 200:
        return response.json().get("solana", {}).get("usd", 1)
    return -1


def get_ton_usd_rate():
    url = f"https://tonapi.io/v2/rates"
    params = {
        "tokens": "ton",
        "currencies": "usd",
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        if data:
            try:
                return data.get("rates", {}).get("TON", {}).get("prices", {}).get("USD", {})
            except ValueError:
                raise ValueError("Курс TON/USD не найден.")
        else:
            raise ValueError(f"Ошибка в API: {data.get('error')}")
    except requests.RequestException as e:
        raise SystemExit(f"Ошибка соединения: {e}")
    except ValueError as e:
        raise SystemExit(f"Ошибка данных: {e}")


def get_bnb_usd_rate():
    response = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=binancecoin&vs_currencies=usd")
    if response.status_code == 200:
        return response.json().get("binancecoin", {}).get("usd", 1)
    return -1


def get_eth_usd_rate():
    """
    Получение текущего курса ETH/USD.
    """
    response = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd")
    if response.status_code == 200:
        return response.json().get("ethereum", {}).get("usd", 1)
    return -1


def get_trx_usd_rate():
    """
    Получение курса TRX/USD.
    """
    response = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=tron&vs_currencies=usd")
    if response.status_code == 200:
        return response.json().get("tron", {}).get("usd", 1)
    return -1



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
        return response.json().get("result", [])

    def get_last_token_transactions(self, wallet_address, contract_address, limit=3):
        url = (
            f"{self.api_url}?module=account&action=tokentx"
            f"&contractaddress={contract_address}&address={wallet_address}"
            f"&apikey={self.api_key}&sort=desc&page=1&offset=3"
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
        return response.json().get("result", [])

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
            f"https://apilist.tronscanapi.com/api/token_trc20/transfers"
            f"?contract_address={contract_address}"  # Адрес контракта TRC20
            f"&relatedAddress={wallet_address}"  # Адрес кошелька
            f"&sort=-timestamp"  # Сортировка по времени (новейшие транзакции сначала)
            f"&limit={limit}"  # Количество транзакций на странице
            f"&start=0"  # Начальный индекс для пагинации
        )
        response = requests.get(url)
        response.raise_for_status()
        return response.json().get("token_transfers", [])

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
        elif blockchain == "Base":
            return BaseApi(api_key=os.getenv("BASE_API_KEY"))
        else:
            raise ValueError(f"Блокчейн {blockchain} не поддерживается.")


def is_transaction_valid(received_amount, expected_amount, tolerance=0.001):
    """
    Проверяет, попадает ли сумма в допустимый диапазон.
    """
    return abs(received_amount - expected_amount) <= (expected_amount * tolerance)


def check_payment(blockchain, expected_amount, token_contract=None, tolerance=0.001):
    """
    Универсальная проверка транзакций.
    """
    blockchain_api = BlockchainFactory.get_blockchain_api(blockchain)
    wallet_address = os.environ.get(f"{blockchain}_WALLET_ADDRESS")
    if token_contract:
        transactions = blockchain_api.get_last_token_transactions(wallet_address, token_contract)
        for tx in transactions:
            if blockchain == "TRON":
                amount = float(tx.get('quant')) / 1e6
                tx_hash = tx.get('transaction_id')
            elif blockchain == "BSC" or blockchain == "Base":
                amount = float(tx.get("value")) / 1e18
                tx_hash = tx.get("hash")
            if is_transaction_valid(amount, expected_amount, tolerance):
                return True, tx_hash
        return False, None

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
            try:
                details = blockchain_api.get_transaction_details(tx.get("signature"))
                instructions = details.get("transaction", {}).get("message", {}).get("instructions", [])
                for instruction in instructions:
                    if (instruction.get("programId") == "11111111111111111111111111111111"
                            and instruction.get("parsed", {})
                                    .get("info", {})
                                    .get("destination", "") == os.environ.get("SOL_WALLET_ADDRESS")):
                        amount = float(instruction.get("parsed", {}).get("info", {}).get("lamports", 0)) / 1e9
                        tx_hash = tx.get("signature")
                        if count > 3:
                            break
            except HTTPError:
                print("Too many requests")
                continue
        elif blockchain == "BSC" or blockchain == "BASE":
            amount = float(tx.get("value", 0)) / 1e18
            tx_hash = tx.get("hash")
        elif blockchain == "TRON":
            amount = float(tx.get("contractData").get("amount", 0)) / 1e6
            tx_hash = tx.get("hash")

        if is_transaction_valid(amount, expected_amount, tolerance):
            return True, tx_hash

    return False, None


def validate_payment(transaction):
    """
    Проверка оплаты для переданной транзакции.
    """
    token_contract = None
    if transaction.currency == "USDT" and transaction.blockchain == "BSC":
        token_contract = os.getenv("USDT_BSC_MINT_ADDRESS")
    elif transaction.currency == "USDT" and transaction.blockchain == "TRON":
        token_contract = os.getenv("USDT_TRON_MINT_ADDRESS")
    elif transaction.currency == "USDC" and transaction.blockchain == "Base":
        token_contract = os.getenv("USDC_BASE_MINT_ADDRESS")

    is_valid, tx_id = check_payment(
        blockchain=transaction.blockchain,
        expected_amount=transaction.expected_amount,
        token_contract=token_contract,
    )

    if is_valid:
        transaction.status = "Success"
        transaction.tx_id = tx_id
        session.commit()
        return True
    else:
        return False
