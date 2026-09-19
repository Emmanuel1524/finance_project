# EXP-0014 — decisão: REJECT (NÃO SUSTENTADO; reabertura do EXP-0008 concluída)
Resultado: PF 0.49, WR 40.4%, PnL -R$1268, DD 14.34%, 99 trades, payoff 0.73, expectância -R$12.81, meses + 1/5.
Placebo (10 sorteios): média -R$13.49, p95 -R$4.27, máx -R$3.06: excesso +R$0.68/trade (ruído). 95 de 99 saídas por horário (17:55): a deriva de 25 min é menor que o custo de ida e volta (~R$12).
Conclusão: o EXP-0008 deixa de ser BLOCKED: NÃO SUSTENTADO no WDO nesta amostra e custos provisórios (entrada 17:30, saída 17:55).
Integrity: Look-ahead PASS (fechamento das 09:30 e fechamento anterior; entrada 17:30) | Point-in-time PASS | Replay unchanged YES (janela de sessão 09:00-18:00 é Config do candidato) | New leakage risk NO | Leakage tests: pendente até o fim da run
Overfitting: hipótese estrutural YES (literatura); micro-tuning NO; complexidade justificada YES; estabilidade checada YES (1/5); concentração aceitável YES (top5 36.2%); validação consultada NO; premissa desafiada YES (janela livre, D9); placebo reportado YES

## Atualização de integridade (fim da run)
Leakage tests (05 §11) executados: **PASS** (tests/test_candidates_run2_leakage.py, 9 passed).
