# EXP-0010 — decisão: REFINE (uma mudança ESTRUTURAL específica: remover o trailing, stop estrutural da literatura)
Resultado: PF 0.778, WR 40%, PnL -R$995, DD 13.55%, 100 trades, payoff 1.17, expectância -R$9.95, top5 34.9%, meses + 2/5.
Placebo (10 sorteios): expectância média -R$19.9, p95 -R$13.4, máx -R$12.85: o candidato fica ACIMA de todos os sorteios (excesso +R$9.9/trade); ainda < 0 após custos, então reprova só no portão de expectância (e concentração mensal por lucro total <= 0).
Controle vs EXP-0009: a adaptação ao range NÃO se paga (mesmo PnL, DD 13.5% vs 18.0%, excesso 9.9 vs 4.6, 0 vs 1 grau de liberdade) => preferir a versão fixa.
Diagnóstico: 77% das saídas por TRAILING_STOP (distância 10 = stop): whipsaw converte o sinal em perdas; o placebo também perde ~R$20/trade nessa arquitetura.
Integrity: Look-ahead PASS | Point-in-time PASS | Replay unchanged YES | New leakage risk NO | Leakage tests: pendente até o fim da run
Overfitting: hipótese estrutural YES; micro-tuning NO; complexidade justificada YES (0 dof); estabilidade checada YES; concentração aceitável YES (34.9%); validação consultada NO; premissa do V0 desafiada YES; placebo reportado YES

## Atualização de integridade (fim da run)
Leakage tests (05 §11) executados: **PASS** (tests/test_candidates_run2_leakage.py, 9 passed).
