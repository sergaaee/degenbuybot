import requests


def get_balance(wallet_address):
    url = "https://api.mainnet-beta.solana.com"
    data = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getBalance",
        "params": [wallet_address]
    }
    response = requests.post(url, json=data)
    if response.status_code == 200:
        return response.json().get("result", {}).get("value", 0) / 1e9
    return 0


def get_token_balances(wallet_address):
    """
    Получение баланса всех токенов, привязанных к указанному кошельку.
    """
    url = "https://api.mainnet-beta.solana.com"
    data = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getTokenAccountsByOwner",
        "params": [
            wallet_address,
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
    return 1  # Возвращаем 1 как заглушку

#Es9vMFrzaCERkH4MG4u6ecG75Dbfydf4tBhQPgJcx7t
print(get_token_balances("AB995FrQskZWFZMEf6hSnHMonJYk86CPipQN5ny7Y3pr"))