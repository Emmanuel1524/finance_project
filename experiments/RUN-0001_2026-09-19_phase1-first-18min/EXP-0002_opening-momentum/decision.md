# EXP-0002 — decisão: REFINE (mudança estrutural de SAÍDA no mesmo ramo)
Resultado: PF 0.786, PnL -R$940, DD 11.51%, 100 trades, WR 59%, expectância -R$9.40, meses positivos 3/5, top5 trades 14.7% do lucro bruto.
Reprova só em expectância (e concentração mensal por lucro total negativo). Ganha do V0 em PF/DD/PnL.
Achado: com stop 10 / alvo 6 uma entrada sem edge acerta ~62.5% (10/16) e perde ~R$12/trade em custos; V0 (57%) e ORB (59%) ficam abaixo disso:
a estrutura de saída (payoff 0.6) é o gargalo; o ORB tem excesso de ~+R$2.6/trade sobre entrada aleatória (n=100: não significativo).
Integrity checks:
- Look-ahead review: PASS (usa só o corpo da 1ª barra, já fechada, na abertura da 2ª)
- Point-in-time features: PASS
- Replay assumptions unchanged: YES
- New leakage risk introduced: NO
- Leakage tests (05 §11) executed: YES (tests/test_candidates_leakage.py, ver run_report)
Overfitting review:
- Clear structural hypothesis: YES (momentum/ORB, fontes na pesquisa externa)
- Micro-parameter tuning performed: NO
- Added complexity justified: YES (regra única de 1 linha)
- Temporal stability checked: YES (3/5 meses positivos; maio -815 domina a perda)
- PnL concentration acceptable: N/A (lucro total negativo); top5 trades 14.7%
- Validation data consulted unnecessarily: NO
