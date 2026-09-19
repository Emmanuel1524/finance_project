# EXP-0005 — decisão: REFINE (ramo V0-Filters/ablação: PROMISING, com ressalva post-hoc)
Resultado: PF 0.937, WR 61.97%, PnL -R$182, DD 10.97%, 71 trades, expectância -R$2.56, 2/5 meses positivos, rolling20 positivo em 45.6%.
Domina V0, EXP-0001 (PF/PnL) e os demais em PF/PnL/DD; falha só no portão de expectância (e concentração mensal por lucro total <= 0).
Integrity checks:
- Look-ahead review: PASS (só o rótulo de padrão decidido na abertura)
- Point-in-time features: PASS
- Replay assumptions unchanged: YES
- New leakage risk introduced: NO
- Leakage tests (05 §11) executed: YES (tests/test_candidates_leakage.py, ver run_report)
Overfitting review:
- Clear structural hypothesis: YES (seleção adversa em zonas de stop-run), MAS motivada pela decomposição do V0 na pesquisa: risco post-hoc alto
- Micro-parameter tuning performed: NO
- Added complexity justified: YES (remove código; 0 parâmetros)
- Temporal stability checked: YES (fev +259 ... mai -378; 2/5 positivos)
- PnL concentration acceptable: N/A (lucro total negativo); top5 trades 21.4%
- Validation data consulted unnecessarily: NO
Lições: remover P3 tira a maior fonte de perda; P1_EMA fica ~zero, P2_LOW perde -211, P4_RSI é o único com excesso (13 trades). Exige validação futura (não consultada nesta run).
