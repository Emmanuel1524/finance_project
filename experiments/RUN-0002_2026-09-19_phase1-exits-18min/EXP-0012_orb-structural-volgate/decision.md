# EXP-0012 — decisão: INCONCLUSIVE (data-informed; melhor resultado, MAS reprova nos portões de concentração)
Resultado: PF 1.414, WR 28.9%, PnL +R$1530, DD 14.26% (passa), 45 trades, payoff 3.48, expectância +R$34.0, meses + 3/5 (fev -445, mar +1788, abr -203, mai +258, jun +132).
Placebo (10 sorteios com o MESMO gate): média -R$41.7, p95 -R$25.2, máx -R$0.11: candidato acima de TODOS os sorteios (excesso +R$75.7/trade).
Portões D3: min_trades OK; DD OK (14.26%); expectância OK; FALHAM top5 trades = 72% do lucro bruto (> 40%) e concentração mensal (março +1788 > lucro total +1530: sem março o resultado é negativo, -R$258).
Interpretação: sinal consistente com o placebo, mas dependente de poucos trades e de um mês; a regra de regime veio da MESMA amostra que a testa (snooping: 4 leituras + esta). Não elegível ao placar. Candidato a checkpoint de validação (consome 1 das 3): decisão do usuário.
Integrity: Look-ahead PASS | Point-in-time PASS (mediana de 20 pregões passados, D7) | Replay unchanged YES | New leakage risk NO | Leakage tests: pendente até o fim da run
Overfitting: hipótese estrutural YES (com ressalva data-informed); micro-tuning NO; complexidade justificada YES (0 dof); estabilidade checada YES (frágil); concentração aceitável NO; validação consultada NO; premissa desafiada YES; placebo reportado YES

## Atualização de integridade (fim da run)
Leakage tests (05 §11) executados: **PASS** (tests/test_candidates_run2_leakage.py, 9 passed).
