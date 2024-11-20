import requests
import os
from dotenv import load_dotenv

load_dotenv()
sol_wallet_address = os.environ.get('SOL_WALLET_ADDRESS')


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
    ton_wallet_address = os.environ.get("TON_WALLET_ADDRESS")

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
