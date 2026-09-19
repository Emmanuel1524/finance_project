# EXP-0004 — decisão: REJECT
Resultado: PF 0.706 (V0 0.75), PnL -R$911, DD 14.74%, 68 trades, WR 57.35%, expectância -R$13.4 (pior que V0), 1/5 meses positivos.
Filtrar contra-tendência remove trades, mas não melhora a qualidade por trade; P1_EMA (30 trades) perde -R$525.
Integrity checks:
- Look-ahead review: PASS (só EMAs D1 de candles fechados e a abertura)
- Point-in-time features: PASS
- Replay assumptions unchanged: YES
- New leakage risk introduced: NO
- Leakage tests (05 §11) executed: YES (tests/test_candidates_leakage.py, ver run_report)
Overfitting review:
- Clear structural hypothesis: YES (com nota: formulada após ver LONG pior que SHORT no V0)
- Micro-parameter tuning performed: NO
- Added complexity justified: NO (não melhora expectância)
- Temporal stability checked: YES (1/5 meses positivos; março -778)
- PnL concentration acceptable: N/A
- Validation data consulted unnecessarily: NO
Lições: alinhamento com a tendência D1 não resolve a falta de edge da entrada; família trend-alignment com 1 rejeição.
