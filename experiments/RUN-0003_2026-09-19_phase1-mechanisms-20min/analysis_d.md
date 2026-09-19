# Análise D — sensibilidade de execução (slippage × custos), partição de pesquisa

| Arquitetura | Slippage (pt/lado) | Custo (R$/contrato/lado) | Trades | Expectância (R$) | PF | PnL (R$) |
|---|---|---|---|---|---|---|
| EXP-0011 (ORB estrutural) | 0.0 | 0.0 | 100 | +12.4 | 1.18 | +1240 |
| EXP-0011 (ORB estrutural) | 0.0 | 1.0 | 100 | +10.4 | 1.15 | +1040 |
| EXP-0011 (ORB estrutural) | 0.5 | 0.0 | 100 | +2.4 | 1.03 | +240 |
| EXP-0011 (ORB estrutural) | 0.5 | 1.0 | 100 | +0.4 | 1.01 | +40 |
| EXP-0011 (ORB estrutural) | 1.0 | 0.0 | 100 | -7.6 | 0.91 | -760 |
| EXP-0011 (ORB estrutural) | 1.0 | 1.0 | 100 | -9.6 | 0.89 | -960 |
| EXP-0012 (+ vol alta, data-informed) | 0.0 | 0.0 | 45 | +46.0 | 1.62 | +2070 |
| EXP-0012 (+ vol alta, data-informed) | 0.0 | 1.0 | 45 | +44.0 | 1.59 | +1980 |
| EXP-0012 (+ vol alta, data-informed) | 0.5 | 0.0 | 45 | +36.0 | 1.45 | +1620 |
| EXP-0012 (+ vol alta, data-informed) | 0.5 | 1.0 | 45 | +34.0 | 1.41 | +1530 |
| EXP-0012 (+ vol alta, data-informed) | 1.0 | 0.0 | 45 | +26.0 | 1.30 | +1170 |
| EXP-0012 (+ vol alta, data-informed) | 1.0 | 1.0 | 45 | +24.0 | 1.27 | +1080 |

Cenário base (D6 provisório): slippage 0,5 e custo 1,0. Leitura: a diferença entre a linha (0; 0) e o base mostra quanto do resultado é consumido pela execução.
