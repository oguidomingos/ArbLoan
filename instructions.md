Para que o teste “Deve proteger contra ataques de reentrância” realmente dispare o ReentrancyGuard, você precisa garantir que a sua função de arbitragem passe do check de lucro e chegue à parte que, em tese, tentaria um segundo chamado interno via callback malicioso. No momento, o mock de Uniswap está fazendo a sua arbitragem “não dar lucro” e, por isso, o revert ocorre antes do guardião de reentrância:
	1.	Entenda o fluxo do teste
No seu ArbitrageBot.test.js, a seção de reentrância provavelmente faz algo assim:
	•	Configura um router “honesto” que retorna valores lucrativos.
	•	Configura um router malicioso que, no transfer, tenta chamar de volta arbitrage().
	•	Chama arbitrage() e espera que, no segundo swap (ou no transfer do token), o nonReentrant lance “ReentrancyGuard: reentrant call”.
Mas, se o return dos swaps não gera lucro, a função já estoura em require(profit > 0, "No profit made") antes de chegar ao callback.
	2.	Ajuste os mocks para simular lucro
Abra o trecho do teste onde você instancia o mock do primeiro router e define os return amounts.

// Exemplo hipotético de configuração
await router1.setAmounts(inputAmount, outputAmount);   // swap “ida”
await router2.setAmounts(outputAmount, finalAmount);   // swap “volta”

Garanta que finalAmount > inputAmount para que profit = finalAmount - inputAmount seja positivo. Por exemplo:

await router1.setAmounts(100, 200);   // 100 → 200 na ida
await router2.setAmounts(200, 250);   // 200 → 250 na volta  (lucro = 150)

Com isso, a require(profit > 0) passa, e o próprio transfer do token malicioso é disparado, provocando a reentrância.

	3.	Confirme que o modifier nonReentrant está aplicado
No seu ArbitrageBot.sol, verifique se a função principal de arbitragem (por exemplo, executeArbitrage) está marcada com nonReentrant do OpenZeppelin:

function executeArbitrage(...) external onlyOwner nonReentrant {
    // ...
}

Se não estiver, adicione o modifier. Ele precisa envolver todo o corpo do método.

	4.	Rode o teste novamente
Depois de ajustar os valores mock e confirmar o nonReentrant, execute:

npx hardhat test test/ArbitrageBot.test.js --grep "reentrância"

Agora, com lucro simulado, o callback malicioso deverá acionar o guardião e a transação deve reverter com “ReentrancyGuard: reentrant call”.

	5.	Alternativa: alterar a ordem dos require
Se, por motivo de arquitetura, você quiser que o teste dispare o guard antes do check de lucro, você precisaria inverter a ordem na função:

nonReentrant
function executeArbitrage(...) external onlyOwner {
    // 1) lock reentrancy
    // 2) executar swaps
    uint256 profit = ...;
    require(profit > 0, "No profit made");
}

Mas isso é menos usual – o padrão é manter o check de lucro e usar mocks lucrativos.

⸻

Resumo: o erro “No profit made” significa que o cenário de teste não gerou lucro e portanto a função nunca alcançou o ponto em que a reentrância aconteceria. Ajuste os valores de retorno do seu mock router para garantir profit > 0 e confirme que o método está protegido com nonReentrant. Aí sim, o teste deverá capturar corretamente o revert “ReentrancyGuard: reentrant call”.