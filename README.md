# Arbitrage Bot

Bot de arbitragem automatizada entre DEXs na rede Polygon, utilizando flash loans do Aave para maximizar oportunidades.

## Arquitetura

Veja a documentação completa da arquitetura em [docs/arbitrage-architecture.md](docs/arbitrage-architecture.md).

## Pré-requisitos

- Node.js >= 14
- Python >= 3.8
- Conta com MATIC para gas

## Instalação

1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/arb-loan
cd arb-loan
```

2. Instale as dependências do contrato:
```bash
npm install
```

3. Instale as dependências Python:
```bash
pip install -r requirements.txt
```

4. Configure as variáveis de ambiente:
```bash
cp .env.example .env
```

Edite o arquivo .env com suas configurações:
```
# RPC e Contratos
WEB3_PROVIDER=https://polygon-rpc.com
CONTRACT_ADDRESS=seu_endereco_contrato
PRIVATE_KEY=sua_chave_privada

# APIs
PARASWAP_API_KEY=sua_chave_paraswap

# Configurações
MIN_PROFIT_THRESHOLD=0.1  # Lucro mínimo em % após taxas
GAS_PRICE_MULTIPLIER=1.1  # Multiplicador de gas para transações rápidas
```

## Testes

### Testes do Contrato

```bash
# Roda testes unitários
npx hardhat test

# Roda análise de segurança
npx hardhat run scripts/security-check.js
```

### Testes do Monitor

```bash
# Roda testes unitários Python
python -m pytest tests/

# Roda testes de integração
python -m pytest tests/integration/
```

## Deploy

1. Deploy do contrato:
```bash
npx hardhat run scripts/deploy.js --network polygon
```

2. Atualize o endereço do contrato no .env após o deploy

## Execução

1. Inicie o monitor:
```bash
python monitor.py
```

O monitor irá:
- Monitorar preços dos pares configurados
- Detectar oportunidades de arbitragem
- Executar trades quando lucrativo
- Registrar eventos em logs/arbitrage.log

## Monitoramento

### Logs

Os logs são salvos em formato JSON em `logs/arbitrage.log`:
```json
{
  "timestamp": "2024-04-22T11:00:00",
  "level": "INFO",
  "event": "opportunity_found",
  "data": {
    "pair": "USDC/WETH",
    "profit": "0.15%",
    "gas_cost": "10 MATIC"
  }
}
```

### Métricas

Métricas são expostas em `/metrics` para coleta via Prometheus:
- `arb_opportunities_total`: Contador de oportunidades detectadas
- `arb_trades_total`: Contador de trades executados
- `arb_profit_total`: Lucro total realizado em USD
- `api_latency_seconds`: Latência das chamadas à API

## Segurança

O contrato utiliza:
- OpenZeppelin para controles de acesso e operações seguras com tokens
- ReentrancyGuard contra ataques de reentrada
- Análise estática via Slither
- Testes de integração com fork da mainnet

## Contribuindo

1. Fork o repositório
2. Crie uma branch para sua feature (`git checkout -b feature/nome`)
3. Commit suas mudanças (`git commit -am 'Adiciona feature'`)
4. Push para a branch (`git push origin feature/nome`)
5. Abra um Pull Request

## Licença

MIT