# EXP-0007 — decisão: REJECT (amostra insuficiente e sem edge)
Resultado: PF 0.738, WR 52.9%, PnL -R$224, DD 4.84%, 17 trades (< 30), expectância -R$13.18; top5 trades 66.5% do lucro bruto; grupos de regime inconclusivos (< 15 trades).
Sem o IFR o acerto cai de 69% (P4, n=13) para 53% (n=17): a exaustão por posição relativa ao range não basta, ou o acerto do P4 foi ruído amostral.
Integrity checks:
- Look-ahead review: PASS (só abertura vs PDH/PDL do dia anterior)
- Point-in-time features: PASS
- Replay assumptions unchanged: YES
- New leakage risk introduced: NO
- Leakage tests (05 §11) executed: YES (tests/test_candidates_leakage.py, ver run_report)
Overfitting review:
- Clear structural hypothesis: YES (mas derivada da decomposição do V0)
- Micro-parameter tuning performed: NO
- Added complexity justified: N/A (regra simples)
- Temporal stability checked: YES (2/5 meses, amostra pequena)
- PnL concentration acceptable: NO (top5 66.5%)
- Validation data consulted unnecessarily: NO
