# EXP-0003 — decisão: REJECT (ramo Opening-Momentum FECHADO)
Resultado: PF 0.775, WR 30.3%, PnL -R$1683, DD 23.99%, 99 trades, expectância -R$17.0, 0/5 meses positivos, pior trade -R$197 (gap além do stop).
Com stop 10 / alvo 20 uma entrada aleatória acertaria ~33.3%; o ORB acerta 30.3%: sem excesso de edge. Piora PnL, DD e estabilidade vs pai.
Integrity checks:
- Look-ahead review: PASS
- Point-in-time features: PASS
- Replay assumptions unchanged: YES (só gain_points do candidato; motor, custos e política intrabar iguais)
- New leakage risk introduced: NO
- Leakage tests (05 §11) executed: YES (tests/test_candidates_leakage.py, ver run_report)
Overfitting review:
- Clear structural hypothesis: YES (perfil de payoff)
- Micro-parameter tuning performed: NO (uma única variante estrutural 2:1; sem busca)
- Added complexity justified: YES (nenhuma regra nova)
- Temporal stability checked: YES (0/5 meses positivos)
- PnL concentration acceptable: N/A
- Validation data consulted unnecessarily: NO
Lições: ORB de 5 min (corpo da 1ª barra) não mostra edge no WDO nesta amostra, nem com payoff 0.6 nem 2:1. Ramo fechado; reabrir só com racional novo (ex.: filtro de 'stocks in play' equivalente).
