# EXP-0008 — decisão: REJECT (DESIGN INVÁLIDO: a hipótese não é testável com o motor congelado)
Resultado: PF 0.651, WR 55.56%, PnL -R$2338, DD 26.95%, 99 trades, expectância -R$23.62, pior trade -R$642.
A hipótese pede sair perto do fechamento; o motor 1.0.0 só tem stop/alvo fixos (10/6), sem saída por horário. As posições atravessam a noite e o
resultado é dominado por gaps (pior trade -64 pts). NADA se conclui sobre o momentum de Gao et al. no WDO. Reabrir só se o usuário aprovar uma
capacidade de saída por horário no motor (mudança de motor = tarefa separada, 05 §10).
Integrity checks:
- Look-ahead review: PASS (só fechamentos de barras já fechadas; fechamento da sessão anterior)
- Point-in-time features: PASS
- Replay assumptions unchanged: YES (janela de sessão 09:00-18:00 é Config do candidato; motor/custos/política intrabar iguais)
- New leakage risk introduced: NO
- Leakage tests (05 §11) executed: N/A (cenário sintético termina às 12:55 e nunca chega às 17:30; revisão de código: sem uso de barra corrente/futura)
Overfitting review:
- Clear structural hypothesis: YES (literatura)
- Micro-parameter tuning performed: NO
- Added complexity justified: N/A
- Temporal stability checked: YES (1/5 meses positivos; abril -1600 por gap)
- PnL concentration acceptable: N/A
- Validation data consulted unnecessarily: NO
