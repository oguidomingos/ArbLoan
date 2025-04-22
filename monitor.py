import requests
import time
import web3  # Para interação com o contrato inteligente
import json
import random

# Configurações
PARASWAP_API_URL = "https://api.paraswap.io/prices"
CHAIN_ID = 137  # Polygon
WEB3_PROVIDER = "https://polygon-rpc.com"  # Substitua pelo seu provedor
CONTRACT_ADDRESS = "0x3200B6CF57216Ad2F2f34391d7AcC9F9409459D3"  # Endereço do contrato ArbitrageBot

# Lista com 20 pares de tokens para monitorar (endereços de tokens na Polygon)
PAIRS = [
    {"srcToken": "0xD6DF932A45C0f255f85145f286eA0b292B21C90B", "destToken": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"},  # AAVE/USDC
    {"srcToken": "0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6", "destToken": "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619"},  # WBTC/WETH
    {"srcToken": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174", "destToken": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F"},  # USDC/USDT
    {"srcToken": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174", "destToken": "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619"},  # USDC/WETH
    {"srcToken": "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619", "destToken": "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270"},  # WETH/MATIC
    {"srcToken": "0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063", "destToken": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"},  # DAI/USDC
]

# Inicializar Web3
w3 = web3.Web3(web3.HTTPProvider(WEB3_PROVIDER))
# Configurar contrato (substitua pelo ABI real)
# contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=[...])

def get_prices(src_token, dest_token, side="SELL", route=None, other_exchange_prices=False, retry_count=0):
    # Exponential backoff em caso de erro
    if retry_count > 0:
        wait_time = min(60, 2 ** retry_count) + random.uniform(0, 1)  # Max 60 segundos + jitter
        print(f"Aguardando {wait_time:.2f} segundos antes de tentar novamente...")
        time.sleep(wait_time)

    params = {
        "srcToken": src_token,
        "destToken": dest_token,
        "amount": "100000000",
        "network": CHAIN_ID,
        "side": side,
        "otherExchangePrices": str(other_exchange_prices).lower()
    }

    if route:
        params["route"] = "-".join(route)

    url = PARASWAP_API_URL + "?" + "&".join([f"{k}={v}" for k, v in params.items()])
    response = None
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Erro na requisição: {e}")
        if response is not None:
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                x_ratelimit_reset = response.headers.get("X-RateLimit-Reset")
                print(f"  Retry-After: {retry_after}")
                print(f"  X-RateLimit-Reset: {x_ratelimit_reset}")
                if retry_count < 5:  # Máximo de 5 tentativas
                    print(f"  Tentativa {retry_count + 1}/5...")
                    time.sleep(min(60, 2 ** retry_count))  # Backoff exponencial
                    return get_prices(src_token, dest_token, side, route, other_exchange_prices, retry_count + 1)
            elif response.status_code == 404:
                print("  Recurso não encontrado (404)")
            elif response.status_code == 400:
                print("  Requisição inválida (400)")
            else:
                print(f"  Status code: {response.status_code}")
    except Exception as e:
        print(f"Erro inesperado: {e}")
    return None
def detect_arbitrage(data):
    if not data or "priceRoute" not in data:
        return None

    price_route = data["priceRoute"]
    token_in = price_route["srcToken"]
    token_out = price_route["destToken"]
    gas_usd = price_route["gasCostUSD"]
    src_amount = price_route["srcAmount"]
    dest_amount = price_route["destAmount"]
    best_route = price_route["bestRoute"]

    # Calcular a diferença percentual dos preços (exemplo)
    src_usd = float(price_route["srcUSD"])
    dest_usd = float(price_route["destUSD"])
    if src_usd == 0:
        price_difference_percent = 0
    else:
        price_difference_percent = ((dest_usd - src_usd) / src_usd) * 100

    return {
        "tokenIn": token_in,
        "tokenOut": token_out,
        "gasUSD": gas_usd,
        "srcAmount": src_amount,
        "destAmount": dest_amount,
        "bestRoute": best_route,
        "priceDifferencePercent": price_difference_percent
    }

def trigger_arbitrage(pair, buy_dex, sell_dex, amount):
    return "Arbitragem não implementada"

def main():
    TOKEN_NAMES = {
        "0xc2132d05d31c914a87c6611c10748aeb04b58e8f": "USDT",
        "0x0d500b1d8e8ef31e21c99d1db9a6444d3adf1270": "WMATIC",
        "0x7ceb23fd6bc0add59e62ac25578270cff1b9f619": "WETH",
        "0x2791bca1f2de4661ed88a30c99a7a9449aa84174": "USDC",
        "0x1bfd67037b42cf73acf2047067bd4f2c47d9bfd6": "WBTC",
        "0xd6df932a45c0f255f85145f286ea0b292b21c90b": "AAVE",
        "0x831753dd7087cac61ab5644b308642cc1c33dc13": "QUICK",
        "0xbbba073c31bf03b8d0d9b09a2e8a65f810b4348e": "SUSHI"
    }

    print("Iniciando monitoramento de preços...")
    print(f"Monitorando {len(PAIRS)} pares de tokens")
    print("Taxa de atualização: máximo de 1 requisição por segundo")
    print("Usando backoff exponencial para lidar com limites de taxa")
    print("-" * 50)

    while True:
        for pair in PAIRS:
            try:
                # Teste SELL com outras exchanges
                print("\nTestando SELL com outras exchanges:")
                data = get_prices(pair['srcToken'], pair['destToken'],
                                side="SELL",
                                other_exchange_prices=True)
                
                # Teste BUY com rota específica
                print("\nTestando BUY com rota específica:")
                route = [pair['srcToken'], "0x0d500b1d8e8ef31e21c99d1db9a6444d3adf1270", pair['destToken']]  # Rota via WMATIC
                data_buy = get_prices(pair['srcToken'], pair['destToken'],
                                    side="BUY",
                                    route=route,
                                    other_exchange_prices=True)

                if data_buy and "priceRoute" in data_buy:
                    data = data_buy  # Usa os dados da última requisição para o processamento existente
                
                if data and "priceRoute" in data:
                    price_route = data["priceRoute"]
                    src_token = price_route["srcToken"]
                    dest_token = price_route["destToken"]
                    src_token_name = TOKEN_NAMES.get(src_token.lower(), "Unknown")
                    dest_token_name = TOKEN_NAMES.get(dest_token.lower(), "Unknown")
                    gas_usd = price_route["gasCostUSD"]
                    src_amount = price_route["srcAmount"]
                    dest_amount = price_route["destAmount"]
                    best_route = price_route["bestRoute"]
                    src_usd = float(price_route["srcUSD"])
                    dest_usd = float(price_route["destUSD"])

                    # Extract exchange names and rates from the best route
                    exchange_info = []
                    for route in best_route:
                        for swap in route["swaps"]:
                            for exchange in swap["swapExchanges"]:
                                exchange_info.append({
                                    "name": exchange["exchange"],
                                    "rate": exchange.get("rate", "N/A")
                                })

                    # Verificar preços de outras exchanges
                    other_exchanges = []
                    if "others" in data:
                        for exchange_name, info in data["others"].items():
                            if isinstance(info, dict) and "rate" in info:
                                other_exchanges.append({
                                    "name": exchange_name,
                                    "rate": info["rate"]
                                })

                    # Calculate price difference percent
                    if src_usd == 0:
                        price_difference_percent = 0
                    else:
                        price_difference_percent = ((dest_usd - src_usd) / src_usd) * 100

                    print("\nDetalhes da rota:")
                    print(f"  Token In: {src_token_name} ({src_token})")
                    print(f"  Token Out: {dest_token_name} ({dest_token})")
                    print(f"  Gas USD: {gas_usd}")
                    print(f"  Source Amount: {src_amount}")
                    print(f"  Destination Amount: {dest_amount}")
                    print(f"  Price Difference: {price_difference_percent:.2f}%")
                    
                    print("\nMelhores exchanges na rota:")
                    for ex in exchange_info:
                        print(f"  {ex['name']}: Taxa = {ex['rate']}")
                    
                    if other_exchanges:
                        print("\nPreços em outras exchanges:")
                        for ex in other_exchanges:
                            print(f"  {ex['name']}: Taxa = {ex['rate']}")
                    
                    print("-" * 50)
                else:
                    print(f"Erro ao obter preços para {pair['srcToken']}/{pair['destToken']}")
            except requests.exceptions.RequestException as e:
                print(f"Erro na requisição para {pair['srcToken']}/{pair['destToken']}: {e}")
                if response is not None:
                    if response.status_code == 429:
                        retry_after = response.headers.get("Retry-After")
                        x_ratelimit_reset = response.headers.get("X-RateLimit-Reset")
                        print(f"  Retry-After: {retry_after}")
                        print(f"  X-RateLimit-Reset: {x_ratelimit_reset}")
                    elif response.status_code == 404:
                        print("  Recurso não encontrado (404)")
                    elif response.status_code == 400:
                        print("  Requisição inválida (400)")
            
            # Espera 3 segundos entre cada par para garantir a taxa máxima de 1 req/s
            time.sleep(3)

if __name__ == "__main__":
    main()