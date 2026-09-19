# EXP-0009 — decisão: REJECT (NÃO SUSTENTADO sob saída adaptativa por range)
Resultado (Research): PF 0.84, WR 30.0%, PnL -R$990, DD 18.02%, 100 trades, payoff 1.96, expectância -R$9.9, meses + 3/5, top5 trades 44.7%.
Placebo (10 sorteios, direção aleatória, mesma saída): expectância média -R$14.5, p95 -R$4.25, máx +R$2.25. Excesso do candidato +R$4.6/trade < 1 erro-padrão (~R$11): indistinguível do acaso. Reprova nos portões: DD 18% > 15%, top-5 44.7% > 40%, expectância < 0.
Saídas: 82% por TRAILING_STOP (stop = trailing = 0,25 × range) — o trailing com a mesma distância do stop retira o trade cedo; perda concentrada em dias de baixa volatilidade (-R$1044 em 52 trades vs +R$54 em 48): com stop escalado pequeno, custo+slippage pesam mais (razão custo/risco) — hipótese de mecanismo, formulada APÓS ver o resultado (data-informed).
Integrity checks:
- Look-ahead review: PASS (range do dia anterior e corpo da 1ª barra fechada; ExitSpec calculada na abertura da 2ª barra)
- Point-in-time features: PASS
- Replay assumptions unchanged: YES
- New leakage risk introduced: NO
- Leakage tests (05 §11) executed: pendente até o fim da run (tests/test_candidates_run2_leakage.py); resultado registrado no run_report
Overfitting review:
- Clear structural hypothesis: YES (literatura + mecanismo; reabertura por mecanismo novo)
- Micro-parameter tuning performed: NO (K=0.25 única alternativa a priori)
- Added complexity justified: NO (a controle fixa decide, EXP-0010)
- Temporal stability checked: YES (fev -1179; 3/5 meses +)
- PnL concentration acceptable: NO (top5 44.7%)
- Validation data consulted unnecessarily: NO
- Baseline assumption challenged with a stated hypothesis: YES (payoff 0.6 fixo)
- Excess over random-entry placebo reported: YES

## Atualização de integridade (fim da run)
Leakage tests (05 §11) executados: **PASS** (tests/test_candidates_run2_leakage.py, 9 passed).
