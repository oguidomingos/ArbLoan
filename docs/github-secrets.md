# Configuração de Secrets no GitHub

Para o pipeline CI/CD funcionar corretamente, é necessário configurar as seguintes secrets no GitHub:

## Secrets Necessárias

1. **WEB3_PROVIDER**
   - RPC URL da rede Polygon para testes
   - Exemplo: https://polygon-rpc.com
   - Recomendado: Usar um provedor dedicado como Infura ou Alchemy

2. **MUMBAI_RPC**
   - RPC URL da rede Mumbai (testnet)
   - Usado para deploy em staging

3. **POLYGON_RPC**
   - RPC URL da rede Polygon (mainnet)
   - Usado para deploy em produção
   - Recomendado: Usar um provedor dedicado com alto limite de requisições

4. **PRIVATE_KEY**
   - Chave privada da conta que fará os deploys
   - ⚠️ IMPORTANTE: Use uma conta dedicada apenas para deploys
   - Nunca compartilhe ou exponha esta chave

5. **PARASWAP_API_KEY**
   - Chave de API do ParaSwap
   - Usado nos testes de integração

## Como Configurar

1. Acesse as configurações do repositório no GitHub
   ```
   Settings > Secrets and variables > Actions
   ```

2. Clique em "New repository secret"

3. Adicione cada secret com seu respectivo valor

4. Para ambientes específicos (staging/production):
   ```
   Settings > Environments > New environment
   ```
   - Crie ambientes "staging" e "production"
   - Adicione proteções como aprovação necessária para deploys em produção

## Variáveis de Ambiente por Ambiente

### Staging (Mumbai)
- `ENVIRONMENT=staging`
- Usar `MUMBAI_RPC`
- Configurar limites menores para arbitragem

### Production (Polygon)
- `ENVIRONMENT=production`
- Usar `POLYGON_RPC`
- Requer aprovação para deploy
- Monitoramento ativo 24/7

## Segurança

- Nunca compartilhe ou exponha as chaves privadas
- Use contas dedicadas para cada ambiente
- Limite o acesso às secrets apenas para administradores
- Revogue e rotacione as chaves periodicamente
- Monitore os logs de acesso às secrets
- Configure proteções de branch para evitar deploys acidentais

## Monitoramento

O pipeline está configurado para:
1. Executar testes antes de cada deploy
2. Verificar segurança do contrato com Slither
3. Criar PR para review antes do deploy em staging
4. Requerer aprovação para deploy em produção
5. Criar release com endereço do contrato após deploy

## Troubleshooting

Se o pipeline falhar, verifique:
1. Se todas as secrets estão configuradas
2. Se os RPCs estão respondendo
3. Se a conta tem fundos suficientes para deploy
4. Logs de erro no Actions
5. Configurações de ambiente (staging/production)