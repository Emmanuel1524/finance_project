# EXP-0015 — decisão: REJECT (NÃO SUSTENTADO)
Resultado: PF 0.877, WR 49.3%, PnL -R$472, DD 12.86%, 71 trades, payoff 0.90, expectância -R$6.65, meses + 3/5, top5 17.5%.
Pai EXP-0005 (10/6): PnL -R$182, expectância -R$2.56: o payoff 1:1 NÃO melhorou (pior). Placebo (10 sorteios): média -R$14.62, máx -R$2.56; excesso +R$8 (~1 erro-padrão, não distinguível).
Só o P4_RSI é positivo (+R$424, 13 trades, WR 69%); P1_EMA (32 trades) -R$579.
Integrity: Look-ahead PASS | Point-in-time PASS | Replay unchanged YES | New leakage risk NO | Leakage tests: pendente até o fim da run
Overfitting: hipótese estrutural YES (mecanismo de payoff); micro-tuning NO; complexidade justificada YES (0 dof); estabilidade checada YES; concentração aceitável YES; validação consultada NO; premissa desafiada YES (payoff 0.6); placebo reportado YES

## Atualização de integridade (fim da run)
Leakage tests (05 §11) executados: **PASS** (tests/test_candidates_run2_leakage.py, 9 passed).
