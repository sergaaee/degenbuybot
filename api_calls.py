import requests
import os
from dotenv import load_dotenv

load_dotenv()
sol_wallet_address = os.environ.get('SOL_WALLET_ADDRESS')
bsc_wallet_address = os.environ.get('BSC_WALLET_ADDRESS')
ton_wallet_address = os.environ.get("TON_WALLET_ADDRESS")
tron_wallet_address = os.environ.get('TRON_WALLET_ADDRESS')


def get_sol_balance():
    url = "https://api.mainnet-beta.solana.com"
    data = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getBalance",
        "params": [sol_wallet_address]
    }
    response = requests.post(url, json=data)
    if response.status_code == 200:
        return response.json().get("result", {}).get("value", 0) / 1e9
    return 0


def get_sol_token_balances():
    """
    Получение баланса всех токенов, привязанных к указанному кошельку.
    """
    url = "https://api.mainnet-beta.solana.com"
    data = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getTokenAccountsByOwner",
        "params": [
            sol_wallet_address,
            {"programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"},  # Программа токенов SPL
            {"encoding": "jsonParsed"}
        ]
    }
    response = requests.post(url, json=data)
    if response.status_code == 200:
        result = response.json().get("result", {}).get("value", [])
        token_balances = {}
        for token_account in result:
            token_info = token_account.get("account", {}).get("data", {}).get("parsed", {})
            token_amount = token_info.get("info", {}).get("tokenAmount", {})
            token_mint = token_info.get("info", {}).get("mint", "Unknown")
            token_balances[token_mint] = float(token_amount.get("uiAmount", 0))
        return token_balances
    return {}


def get_sol_usd_rate():
    response = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=solana&vs_currencies=usd")
    if response.status_code == 200:
        return response.json().get("solana", {}).get("usd", 1)
    return -1


def get_ton_balance():
    url = f"https://toncenter.com/api/v2/getAddressInformation"
    params = {
        "address": ton_wallet_address,
        "api_key": os.environ.get("TON_API_KEY"),
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        if data.get("ok"):
            # Баланс возвращается в нанотонах, конвертируем в TON
            balance_in_ton = int(data["result"]["balance"]) / 10 ** 9
            return balance_in_ton
        else:
            raise ValueError(f"Ошибка в API: {data.get('error')}")
    except requests.RequestException as e:
        raise SystemExit(f"Ошибка соединения: {e}")
    except ValueError as e:
        raise SystemExit(f"Ошибка данных: {e}")


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


def get_bnb_balance():
    url = f"https://api.bscscan.com/api"
    params = {
        "module": "account",
        "action": "balance",
        "address": bsc_wallet_address,
        "apikey": os.environ.get("BSC_API_KEY"),
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        balance_wei = int(response.json().get("result", 0))
        return balance_wei / 1e18  # Конвертируем из Wei в BNB
    return -1


def get_bnb_usd_rate():
    response = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=binancecoin&vs_currencies=usd")
    if response.status_code == 200:
        return response.json().get("binancecoin", {}).get("usd", 1)
    return -1


def get_usdt_bnb_balance():
    # Получаем баланс USDT через BSC API
    url = f"https://api.bscscan.com/api"
    params = {
        "module": "account",
        "action": "tokenbalance",
        "contractaddress": "0x55d398326f99059ff775485246999027b3197955",  # Укажите контракт USDT на BSC
        "address": bsc_wallet_address,
        "apikey": os.environ.get("BSC_API_KEY"),
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        balance_wei = int(response.json().get("result", 0))
        return balance_wei / 1e18  # Конвертируем из Wei в USDT
    return -1


def get_base_eth_balance():
    """
    Получение баланса ETH на сети Base.
    """
    url = f"https://api.basescan.org/api"
    params = {
        "module": "account",
        "action": "balance",
        "address": os.environ.get("BASE_WALLET_ADDRESS"),
        "apikey": os.environ.get("BASE_API_KEY"),
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        balance_wei = int(response.json().get("result", 0))
        return balance_wei / 1e18  # Конвертация из Wei в ETH
    return 0


def get_base_usdc_balance():
    """
    Получение баланса USDC на сети Base.
    """
    url = f"https://api.basescan.org/api"
    params = {
        "module": "account",
        "action": "tokenbalance",
        "contractaddress": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",  # Укажите адрес контракта USDC в сети Base
        "address": os.environ.get("BASE_WALLET_ADDRESS"),
        "apikey": os.environ.get("BASE_API_KEY"),
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        balance_wei = int(response.json().get("result", 0))
        return balance_wei / 1e6  # Конвертация из минимальной единицы в USDC
    return 0


def get_eth_usd_rate():
    """
    Получение текущего курса ETH/USD.
    """
    response = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd")
    if response.status_code == 200:
        return response.json().get("ethereum", {}).get("usd", 1)
    return -1


def get_trx_balance():
    """
    Получение баланса TRX на сети TRON.
    """
    url = f"https://apilist.tronscanapi.com/api/account"
    params = {
        "address": tron_wallet_address,
        "apikey": os.environ.get("TRON_API_KEY"),
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        result = response.json()
        if result and "balance" in result:
            return result["balance"] / 1e6  # Конвертируем из Sun в TRX
    return 0


def get_usdt_trx_balance():
    """
    Получение баланса USDT на сети TRON.
    """
    url = f"https://apilist.tronscanapi.com/api/account/tokens"
    params = {
        "address": tron_wallet_address,
        "apikey": os.environ.get("TRON_API_KEY"),
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        result = response.json()
        for token in result.get("tokens", []):
            if token.get("tokenName") == "Tether USD":
                return float(token.get("balance", 0)) / 1e6  # Конвертация в USDT
    return 0


def get_trx_usd_rate():
    """
    Получение курса TRX/USD.
    """
    response = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=tron&vs_currencies=usd")
    if response.status_code == 200:
        return response.json().get("tron", {}).get("usd", 1)
    return -1
