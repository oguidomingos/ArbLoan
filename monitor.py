import os
import requests
import time
import random
from web3 import Web3
from eth_account import Account
import json
from dotenv import load_dotenv
from utils.logger import arb_logger

# Carregar variáveis de ambiente
load_dotenv()

# Configurações
PARASWAP_API_URL = "https://api.paraswap.io/prices"
CHAIN_ID = 137  # Polygon
WEB3_PROVIDER = os.getenv("WEB3_PROVIDER", "https://polygon-rpc.com")
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
MIN_PROFIT_THRESHOLD = float(os.getenv("MIN_PROFIT_THRESHOLD", "0.1"))
GAS_PRICE_MULTIPLIER = float(os.getenv("GAS_PRICE_MULTIPLIER", "1.1"))

# Lista com pares de tokens para monitorar (endereços de tokens na Polygon)
PAIRS = [
    {"srcToken": "0xD6DF932A45C0f255f85145f286eA0b292B21C90B", "destToken": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"},  # AAVE/USDC
    {"srcToken": "0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6", "destToken": "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619"},  # WBTC/WETH
    {"srcToken": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174", "destToken": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F"},  # USDC/USDT
    {"srcToken": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174", "destToken": "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619"},  # USDC/WETH
    {"srcToken": "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619", "destToken": "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270"},  # WETH/MATIC
    {"srcToken": "0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063", "destToken": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"},  # DAI/USDC
]

# Token names para logging
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

# Inicializar Web3
w3 = Web3(Web3.HTTPProvider(WEB3_PROVIDER))

# Carregar ABI do contrato
with open('config/contracts.json') as f:
    contract_config = json.load(f)
    CONTRACT_ABI = contract_config['abi']

# Configurar contrato
contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=CONTRACT_ABI)

# Configurar conta
account = Account.from_key(PRIVATE_KEY)

def get_prices(src_token, dest_token, side="SELL", route=None, other_exchange_prices=False, retry_count=0):
    start_time = time.time()
    
    # Exponential backoff em caso de erro
    if retry_count > 0:
        wait_time = min(60, 2 ** retry_count) + random.uniform(0, 1)  # Max 60 segundos + jitter
        arb_logger.logger.info(f"Aguardando {wait_time:.2f} segundos antes de tentar novamente...")
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
        end_time = time.time()
        arb_logger.log_api_latency("paraswap_prices", end_time - start_time)
        return response.json()
    except requests.exceptions.RequestException as e:
        arb_logger.logger.error("Erro na requisição", error=str(e))
        if response is not None:
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                x_ratelimit_reset = response.headers.get("X-RateLimit-Reset")
                if retry_count < 5:  # Máximo de 5 tentativas
                    return get_prices(src_token, dest_token, side, route, other_exchange_prices, retry_count + 1)
            elif response.status_code == 404:
                arb_logger.logger.error("Recurso não encontrado (404)")
            elif response.status_code == 400:
                arb_logger.logger.error("Requisição inválida (400)")
            else:
                arb_logger.logger.error(f"Status code: {response.status_code}")
    except Exception as e:
        arb_logger.logger.error("Erro inesperado", error=str(e))
    return None

def detect_arbitrage(data):
    if not data or "priceRoute" not in data:
        return None

    price_route = data["priceRoute"]
    token_in = price_route["srcToken"]
    token_out = price_route["destToken"]
    gas_usd = float(price_route["gasCostUSD"])
    src_amount = price_route["srcAmount"]
    dest_amount = price_route["destAmount"]
    best_route = price_route["bestRoute"]

    # Calcular a diferença percentual dos preços
    src_usd = float(price_route["srcUSD"])
    dest_usd = float(price_route["destUSD"])
    if src_usd == 0:
        price_difference_percent = 0
    else:
        price_difference_percent = ((dest_usd - src_usd) / src_usd) * 100

    # Verificar se a oportunidade é lucrativa após custos
    profit_after_costs = price_difference_percent - gas_usd
    if profit_after_costs < MIN_PROFIT_THRESHOLD:
        return None

    return {
        "tokenIn": token_in,
        "tokenOut": token_out,
        "gasUSD": gas_usd,
        "srcAmount": src_amount,
        "destAmount": dest_amount,
        "bestRoute": best_route,
        "priceDifferencePercent": price_difference_percent,
        "profitAfterCosts": profit_after_costs
    }

def trigger_arbitrage(pair, buy_dex, sell_dex, amount):
    """Executa a arbitragem chamando o contrato inteligente"""
    try:
        # Estimar gas
        gas_estimate = contract.functions.initiateArbitrage(
            pair["tokenIn"],
            pair["tokenOut"],
            amount,
            buy_dex,
            sell_dex
        ).estimate_gas({'from': account.address})
        
        # Obter gas price atual e aplicar multiplicador
        gas_price = int(w3.eth.gas_price * GAS_PRICE_MULTIPLIER)
        
        # Construir transação
        txn = contract.functions.initiateArbitrage(
            pair["tokenIn"],
            pair["tokenOut"],
            amount,
            buy_dex,
            sell_dex
        ).build_transaction({
            'from': account.address,
            'gas': int(gas_estimate * 1.1),  # 10% a mais para segurança
            'gasPrice': gas_price,
            'nonce': w3.eth.get_transaction_count(account.address),
        })
        
        # Assinar e enviar transação
        signed_txn = w3.eth.account.sign_transaction(txn, PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        
        # Aguardar confirmação
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        # Registrar resultado
        if receipt.status == 1:
            arb_logger.log_trade(
                f"{TOKEN_NAMES.get(pair['tokenIn'].lower(), 'Unknown')}/{TOKEN_NAMES.get(pair['tokenOut'].lower(), 'Unknown')}",
                pair["profitAfterCosts"],
                receipt.gasUsed
            )
            return receipt
        else:
            arb_logger.logger.error("Transação falhou", tx_hash=tx_hash.hex())
            return None
            
    except Exception as e:
        arb_logger.logger.error("Erro ao executar arbitragem", error=str(e))
        return None

async def main():
    arb_logger.start_metrics_server(int(os.getenv("PROMETHEUS_PORT", 9090)))
    
    arb_logger.logger.info("Iniciando monitoramento", extra={
        "pairs_count": len(PAIRS),
        "min_profit": MIN_PROFIT_THRESHOLD,
        "chain_id": CHAIN_ID
    })

    while True:
        for pair in PAIRS:
            try:
                # Teste SELL com outras exchanges
                data = get_prices(pair['srcToken'], pair['destToken'],
                               side="SELL",
                               other_exchange_prices=True)
                
                # Teste BUY com rota específica
                route = [pair['srcToken'], "0x0d500b1d8e8ef31e21c99d1db9a6444d3adf1270", pair['destToken']]
                data_buy = get_prices(pair['srcToken'], pair['destToken'],
                                   side="BUY",
                                   route=route,
                                   other_exchange_prices=True)

                if data_buy and "priceRoute" in data_buy:
                    data = data_buy

                if data and "priceRoute" in data:
                    opportunity = detect_arbitrage(data)
                    if opportunity:
                        arb_logger.log_opportunity(
                            f"{TOKEN_NAMES.get(opportunity['tokenIn'].lower(), 'Unknown')}/{TOKEN_NAMES.get(opportunity['tokenOut'].lower(), 'Unknown')}",
                            opportunity['priceDifferencePercent'],
                            opportunity['gasUSD']
                        )
                        
                        # Encontrar as DEXs com melhor spread
                        best_route = opportunity['bestRoute'][0]
                        buy_dex = best_route['swaps'][0]['swapExchanges'][0]['exchange']
                        sell_dex = best_route['swaps'][-1]['swapExchanges'][0]['exchange']
                        
                        # Executar arbitragem
                        result = trigger_arbitrage(opportunity, buy_dex, sell_dex, opportunity['srcAmount'])
                        if result:
                            await arb_logger.notify(
                                f"Arbitragem executada com sucesso!\n" +
                                f"Par: {TOKEN_NAMES.get(opportunity['tokenIn'].lower(), 'Unknown')}/{TOKEN_NAMES.get(opportunity['tokenOut'].lower(), 'Unknown')}\n" +
                                f"Lucro: {opportunity['profitAfterCosts']:.2f}%\n" +
                                f"Gas usado: {result.gasUsed}"
                            )
            
            except Exception as e:
                arb_logger.logger.error("Erro no loop principal", error=str(e))
            
            # Espera entre verificações
            time.sleep(3)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())