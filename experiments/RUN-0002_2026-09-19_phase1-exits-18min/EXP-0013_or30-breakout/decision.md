# EXP-0013 — decisão: REJECT (NÃO SUSTENTADO; abaixo do placebo)
Resultado: PF 0.86, WR 34.7%, PnL -R$1270, DD 25.98% (reprova), 75 trades, payoff 1.62, expectância -R$16.9, meses + 3/5, top5 47.7% (reprova), pior trade -R$367 (stop estrutural largo), SHORT -R$1371 vs LONG +R$101.
Placebo (10 sorteios): média -R$8.97, p95 +R$18.9, máx +R$23.7: o candidato fica ABAIXO da média do acaso (excesso -R$8/trade): o rompimento do range de 30 min não carrega direção útil com esta saída.
Integrity: Look-ahead PASS (range de barras fechadas; entrada na abertura seguinte) | Point-in-time PASS | Replay unchanged YES | New leakage risk NO | Leakage tests: pendente até o fim da run
Overfitting: hipótese estrutural YES (literatura); micro-tuning NO; complexidade justificada YES (0 dof); estabilidade checada YES; concentração aceitável NO; validação consultada NO; premissa desafiada YES; placebo reportado YES
Lição: o sinal do EXP-0011 é o corpo da 1ª barra de 5 min, não o rompimento do range de 30 min; famílias Range-Breakout-30: 1 rejeição.

## Atualização de integridade (fim da run)
Leakage tests (05 §11) executados: **PASS** (tests/test_candidates_run2_leakage.py, 9 passed). O teste revelou que o candidato OR30 não tinha a guarda de stop estrutural do lado protetivo (o motor recusa ExitSpec inválida com ValueError); a guarda foi adicionada e os 75 trades do EXP-0013 permaneceram IDÊNTICOS (a condição inválida nunca ocorreu na partição real).
