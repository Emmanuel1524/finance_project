# EXP-0001 — decisão: REJECT (como candidato isolado); observação mantida como diagnóstico
Resultado: PF 0.846 (V0 0.75), PnL -R$296 (V0 -R$1097), DD 8.67% (V0 16.98%), 43 trades, expectância -R$6.88, meses positivos 1/5.
Domina o V0 em PF/PnL/DD, mas reprova nos portões D3 (expectância <= 0 após custos; lucro total negativo). O V0 continua sem edge nos 43 trades restantes.
Integrity checks:
- Look-ahead review: PASS (usa só ctx.pdh/pdl do dia anterior e range histórico passado)
- Point-in-time features: PASS
- Replay assumptions unchanged: YES
- New leakage risk introduced: NO
- Leakage tests (05 §11) executed: YES (tests/test_candidates_leakage.py, ver run_report)
Overfitting review:
- Clear structural hypothesis: YES (economia custo/stop vs range), porém formulada APÓS decompor o V0 na pesquisa: risco de post-hoc; exige validação futura
- Micro-parameter tuning performed: NO (D7 fixo: janela 20, min_history 10)
- Added complexity justified: YES (1 filtro, 0 parâmetros novos)
- Temporal stability checked: YES (mensal 1/5 positivo; rolling20 positivo em 25%)
- PnL concentration acceptable: N/A (lucro total negativo)
- Validation data consulted unnecessarily: NO
Lições: o filtro de volatilidade remove a maior parte da perda do V0 (regime de baixa vol), mas a lógica de entrada do V0 não tem edge no regime de alta vol. Ramo V0-Filters: EXPLORATORY.
