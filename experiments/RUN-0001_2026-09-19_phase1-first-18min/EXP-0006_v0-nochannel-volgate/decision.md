# EXP-0006 — decisão: REJECT (complexidade não justificada; concentração)
Resultado: PF 0.947, WR 60%, PnL -R$80, DD 7.06%, 35 trades, expectância -R$2.29, 2/5 meses positivos, top5 trades 39.5% do lucro bruto (limite 40%).
Sobre o EXP-0005 (mais simples): melhora marginal de PF (0.937->0.947) e de PnL, mas metade dos trades e concentração muito maior; o ganho vem de 3 trades P4 (+R$214) enquanto o resto perde -R$294.
Integrity checks:
- Look-ahead review: PASS
- Point-in-time features: PASS
- Replay assumptions unchanged: YES
- New leakage risk introduced: NO
- Leakage tests (05 §11) executed: YES (tests/test_candidates_leakage.py, ver run_report)
Overfitting review:
- Clear structural hypothesis: YES (duas causas independentes), mas ambas post-hoc
- Micro-parameter tuning performed: NO
- Added complexity justified: NO (ablação: sem melhora material de robustez sobre EXP-0005)
- Temporal stability checked: YES (2/5 meses)
- PnL concentration acceptable: NO/limítrofe (39.5% vs limite 40%)
- Validation data consulted unnecessarily: NO
