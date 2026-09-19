# EXP-0011 — decisão: REFINE (uma mudança estrutural específica: filtro de regime; ver EXP-0012), NÃO qualificado nos portões
Resultado: PF 1.005, WR 19%, PnL +R$40, DD 24.63%, 100 trades, payoff 4.29, expectância +R$0.4, meses + 3/5 (fev -1714, mar +1206, abr -565, mai +1045, jun +68), top5 55.7%, pior trade -R$267, 17 perdas seguidas.
Placebo (10 sorteios): média -R$25.98, p95 -R$9.1, máx +R$2.9; excesso +R$26.4/trade. Acima do p95, mas um sorteio de 10 supera o candidato e o erro-padrão da expectância (~R$11) é maior que a expectância: indistinguível de zero e do acaso.
Reprova: DD 24.6% > 15%; top5 55.7% > 40%; concentração mensal (mar/mai dominam). LONG +850 vs SHORT -810 (viés direcional da amostra).
Padrão replicado (mesma amostra): baixa vol perde em V0, EXP-0009, 0010, 0011 (-1125, -1044, -794, -939); alta vol: +28, +54, -201, +979.
Integrity: Look-ahead PASS (extremos da 1ª barra fechada; guarda de gap) | Point-in-time PASS | Replay unchanged YES | New leakage risk NO | Leakage tests: pendente até o fim da run
Overfitting: hipótese estrutural YES (literatura); micro-tuning NO; complexidade justificada YES (0 dof); estabilidade checada YES (frágil); concentração aceitável NO; validação consultada NO; premissa desafiada YES; placebo reportado YES

## Atualização de integridade (fim da run)
Leakage tests (05 §11) executados: **PASS** (tests/test_candidates_run2_leakage.py, 9 passed).
