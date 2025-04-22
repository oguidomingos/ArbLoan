from web3 import Web3
import json
import os
from eth_account import Account
import sys

def load_config():
    with open('config/contracts.json', 'r') as f:
        return json.load(f)

def load_contract_abi():
    with open('artifacts/contracts/ArbitrageBot.sol/ArbitrageBot.json', 'r') as f:
        contract_json = json.load(f)
        return contract_json['abi']

def deploy_contract(w3, account, config):
    try:
        # Carregar ABI e Bytecode
        with open('artifacts/contracts/ArbitrageBot.sol/ArbitrageBot.json', 'r') as f:
            contract_json = json.load(f)
            contract_abi = contract_json['abi']
            contract_bytecode = contract_json['bytecode']

        # Criar contrato
        ArbitrageBot = w3.eth.contract(abi=contract_abi, bytecode=contract_bytecode)

        # Construir transação
        construct_txn = ArbitrageBot.constructor(
            config['polygon']['contracts']['aaveLendingPool']
        ).build_transaction({
            'from': account.address,
            'nonce': w3.eth.get_transaction_count(account.address),
            'gas': 2000000,
            'gasPrice': w3.eth.gas_price
        })

        # Assinar e enviar transação
        signed = account.sign_transaction(construct_txn)
        tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
        
        print(f'Transação enviada: {tx_hash.hex()}')
        
        # Aguardar recibo
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        contract_address = tx_receipt.contractAddress
        
        print(f'Contrato implantado em: {contract_address}')

        # Atualizar config com endereço do contrato
        config['polygon']['contracts']['arbitrageBot'] = contract_address
        with open('config/contracts.json', 'w') as f:
            json.dump(config, f, indent=4)

        return contract_address

    except Exception as e:
        print(f'Erro ao implantar contrato: {e}')
        sys.exit(1)

def main():
    # Carregar configurações
    config = load_config()
    
    # Configurar Web3
    w3 = Web3(Web3.HTTPProvider(config['polygon']['network']['rpc']))
    
    # Verificar conexão
    if not w3.is_connected():
        print('Erro: Não foi possível conectar à rede Polygon')
        sys.exit(1)
    
    # Carregar conta do ambiente
    private_key = os.getenv('PRIVATE_KEY')
    if not private_key:
        print('Erro: PRIVATE_KEY não encontrada nas variáveis de ambiente')
        sys.exit(1)
    
    account = Account.from_key(private_key)
    
    # Implantar contrato
    deploy_contract(w3, account, config)

if __name__ == '__main__':
    main()