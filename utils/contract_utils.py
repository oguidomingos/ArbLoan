from web3 import Web3
import json
import os
from eth_account import Account

class ContractManager:
    def __init__(self):
        self.load_config()
        self.setup_web3()
        self.setup_account()
        self.load_contract()

    def load_config(self):
        with open('config/contracts.json', 'r') as f:
            self.config = json.load(f)
            self.network = self.config['polygon']

    def setup_web3(self):
        self.w3 = Web3(Web3.HTTPProvider(self.network['network']['rpc']))
        if not self.w3.is_connected():
            raise Exception("Não foi possível conectar à rede Polygon")

    def setup_account(self):
        private_key = os.getenv('PRIVATE_KEY')
        if not private_key:
            raise Exception("PRIVATE_KEY não encontrada nas variáveis de ambiente")
        self.account = Account.from_key(private_key)

    def load_contract(self):
        contract_address = self.network['contracts']['arbitrageBot']
        if not contract_address:
            raise Exception("Endereço do contrato ArbitrageBot não encontrado na configuração")

        try:
            with open('artifacts/contracts/ArbitrageBot.sol/ArbitrageBot.json', 'r') as f:
                contract_json = json.load(f)
                self.contract_abi = contract_json['abi']
        except Exception as e:
            raise Exception(f"Erro ao carregar ABI do contrato: {e}")

        self.contract = self.w3.eth.contract(
            address=self.w3.to_checksum_address(contract_address),
            abi=self.contract_abi
        )

    def execute_arbitrage(self, token_in, token_out, amount, buy_dex, sell_dex):
        try:
            # Construir transação
            tx = self.contract.functions.initiateArbitrage(
                token_in,
                token_out,
                amount,
                buy_dex,
                sell_dex
            ).build_transaction({
                'from': self.account.address,
                'nonce': self.w3.eth.get_transaction_count(self.account.address),
                'gas': 2000000,
                'gasPrice': self.w3.eth.gas_price
            })

            # Assinar e enviar transação
            signed_tx = self.account.sign_transaction(tx)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)

            # Aguardar recibo
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

            # Processar eventos
            events = self.process_events(receipt)
            
            return {
                'tx_hash': tx_hash.hex(),
                'status': receipt.status,
                'events': events
            }

        except Exception as e:
            raise Exception(f"Erro ao executar arbitragem: {e}")

    def process_events(self, receipt):
        events = []
        for log in receipt.logs:
            try:
                event = self.contract.events.ArbitrageResult().process_log(log)
                events.append({
                    'tokenIn': event.args.tokenIn,
                    'tokenOut': event.args.tokenOut,
                    'profit': event.args.profit,
                    'gasUsed': event.args.gasUsed,
                    'success': event.args.success,
                    'message': event.args.message
                })
            except:
                continue
        return events

    def get_token_address(self, symbol):
        return self.network['tokens'].get(symbol.upper())

    def get_dex_address(self, name):
        return self.network['dexes'].get(name.lower())