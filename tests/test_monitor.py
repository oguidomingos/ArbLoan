import pytest
from unittest.mock import Mock, patch
import json
import os
from datetime import datetime
from web3 import Web3

# Mock das respostas da API
MOCK_PRICE_RESPONSE = {
    "priceRoute": {
        "srcToken": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",  # USDC
        "destToken": "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619",  # WETH
        "srcUSD": "1000.0",
        "destUSD": "1002.0",
        "gasCostUSD": "5.0",
        "srcAmount": "1000000000",  # 1000 USDC (6 decimais)
        "destAmount": "500000000000000000",  # 0.5 WETH (18 decimais)
        "bestRoute": [{
            "swaps": [{
                "swapExchanges": [{
                    "exchange": "QuickSwap",
                    "rate": "0.0005"
                }]
            }]
        }]
    }
}

@pytest.fixture
def mock_web3():
    """Mock do objeto Web3"""
    w3 = Mock()
    w3.eth.contract.return_value = Mock()
    w3.eth.get_block.return_value = {'timestamp': int(datetime.now().timestamp())}
    return w3

@pytest.fixture
def mock_contract(mock_web3):
    """Mock do contrato ArbitrageBot"""
    contract = Mock()
    contract.functions.initiateArbitrage.return_value = Mock()
    return contract

@pytest.fixture
def env_setup():
    """Setup de variáveis de ambiente para testes"""
    os.environ['WEB3_PROVIDER'] = 'http://localhost:8545'
    os.environ['CONTRACT_ADDRESS'] = '0x0000000000000000000000000000000000000000'
    os.environ['MIN_PROFIT_THRESHOLD'] = '0.1'
    yield
    # Cleanup
    os.environ.pop('WEB3_PROVIDER', None)
    os.environ.pop('CONTRACT_ADDRESS', None)
    os.environ.pop('MIN_PROFIT_THRESHOLD', None)

@pytest.mark.asyncio
async def test_get_prices_success():
    """Testa obtenção de preços com sucesso"""
    from monitor import get_prices
    
    with patch('requests.get') as mock_get:
        mock_get.return_value.json.return_value = MOCK_PRICE_RESPONSE
        mock_get.return_value.status_code = 200
        
        result = get_prices(
            "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
            "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619"
        )
        
        assert result == MOCK_PRICE_RESPONSE
        assert 'priceRoute' in result
        assert result['priceRoute']['srcToken'] == "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"

@pytest.mark.asyncio
async def test_get_prices_rate_limit():
    """Testa retry em caso de rate limit"""
    from monitor import get_prices
    
    with patch('requests.get') as mock_get:
        mock_get.return_value.status_code = 429
        mock_get.return_value.headers = {'Retry-After': '1'}
        
        result = get_prices(
            "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
            "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619"
        )
        
        assert result is None
        assert mock_get.call_count > 1  # Verifica se houve retry

def test_detect_arbitrage_profitable():
    """Testa detecção de oportunidade lucrativa"""
    from monitor import detect_arbitrage
    
    result = detect_arbitrage(MOCK_PRICE_RESPONSE)
    
    assert result is not None
    assert result['tokenIn'] == "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
    assert result['tokenOut'] == "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619"
    assert result['priceDifferencePercent'] == pytest.approx(0.2, 0.1)

def test_detect_arbitrage_no_opportunity():
    """Testa quando não há oportunidade"""
    from monitor import detect_arbitrage
    
    data = {
        "priceRoute": {
            **MOCK_PRICE_RESPONSE['priceRoute'],
            "srcUSD": "1000.0",
            "destUSD": "999.0"  # Preço menor = sem oportunidade
        }
    }
    
    result = detect_arbitrage(data)
    
    assert result is not None
    assert result['priceDifferencePercent'] < 0

@pytest.mark.asyncio
async def test_trigger_arbitrage(mock_web3, mock_contract, env_setup):
    """Testa execução de arbitragem"""
    from monitor import trigger_arbitrage
    
    # Setup dos mocks
    buy_dex = "0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff"  # QuickSwap
    sell_dex = "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506"  # SushiSwap
    amount = 1000000000  # 1000 USDC
    
    result = trigger_arbitrage({
        'tokenIn': "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
        'tokenOut': "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619"
    }, buy_dex, sell_dex, amount)
    
    # Por enquanto retorna string pois função não está implementada
    assert isinstance(result, str)
    assert "não implementada" in result

@pytest.mark.asyncio
async def test_main_loop(mock_web3, mock_contract, env_setup):
    """Testa loop principal com mock de todas as dependências"""
    from monitor import main
    
    with patch('monitor.get_prices') as mock_get_prices, \
         patch('monitor.detect_arbitrage') as mock_detect, \
         patch('monitor.trigger_arbitrage') as mock_trigger, \
         patch('time.sleep'):  # Evita delays nos testes
        
        # Setup dos mocks
        mock_get_prices.return_value = MOCK_PRICE_RESPONSE
        mock_detect.return_value = {
            'tokenIn': "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
            'tokenOut': "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619",
            'priceDifferencePercent': 0.2
        }
        mock_trigger.return_value = "Arbitragem não implementada"
        
        # Executa main por algumas iterações
        try:
            with patch('builtins.__import__', side_effect=KeyboardInterrupt):
                main()
        except KeyboardInterrupt:
            pass
        
        # Verifica se as funções principais foram chamadas
        mock_get_prices.assert_called()
        mock_detect.assert_called()