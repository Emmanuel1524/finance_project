# RUN-0002 — Relatório

Tempo usado: 10 min 56 s de 18 min. 8 experimentos; tentativas cumulativas na partição de pesquisa: **16**. Testes de vazamento dos candidatos: **9 passed** (um candidato, OR30, ganhou uma guarda de validade do stop estrutural depois de o teste expor um ValueError do motor; os trades do EXP-0013 permaneceram idênticos).

## Verificação do baseline
V0 sob o motor 1.1.0 = trades idênticos ao EXP-0000 da RUN-0001 (PF 0,75; PnL −R$ 1.097; DD 17,0%; 96 trades).

## Resultados (partição de pesquisa; custos provisórios; placebo = 10 sorteios de direção aleatória com a mesma saída)
| Exp | Candidato | Pai | PF | WR | PnL (R$) | Max DD | Trades | Expectância | Placebo (média) | Excesso | Meses + | Portões D3 | Decisão |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0000 | Baseline V0 | - | 0.75 | 57.29% | -1097.0 | 16.98% | 96 | -11.43 | - | - | 0/5 | não | baseline |
| 0009 | ORB 5min, stop=trailing=0,25×range, sem alvo, saída 17:55 | R1/0002 | 0.84 | 30.0% | -990.0 | 18.02% | 100 | -9.9 | -14.54 | 4.64 | 3/5 | não | REJECT |
| 0010 | Controle fixo: stop=trailing=10 pts | 0009 | 0.778 | 40.0% | -995.0 | 13.55% | 100 | -9.95 | -19.87 | 9.92 | 2/5 | não | REFINE |
| 0011 | ORB 5min, stop estrutural (extremo da 1ª barra), sem trailing | 0010 | 1.005 | 19.0% | 40.0 | 24.63% | 100 | 0.4 | -25.98 | 26.38 | 3/5 | não | REFINE |
| 0012 | EXP-0011 só em regime de vol alta (D7) | 0011 | 1.414 | 28.89% | 1530.0 | 14.26% | 45 | 34.0 | -41.71 | 75.71 | 3/5 | não | INCONCLUSIVE |
| 0013 | Rompimento do range de 30 min, stop estrutural | V0 | 0.86 | 34.67% | -1270.0 | 25.98% | 75 | -16.93 | -8.97 | -7.96 | 3/5 | não | REJECT |
| 0014 | Momentum de fim de dia (17:30→17:55) | R1/0008 | 0.492 | 40.4% | -1268.0 | 14.34% | 99 | -12.81 | -13.49 | 0.68 | 1/5 | não | REJECT |
| 0015 | V0 sem canal, payoff 1:1 (10/10) | R1/0005 | 0.877 | 49.3% | -472.0 | 12.86% | 71 | -6.65 | -14.62 | 7.97 | 3/5 | não | REJECT |
| 0016 | Gap-and-go, stop no fechamento anterior | V0 | 0.722 | 26.14% | -2451.0 | 30.7% | 88 | -27.85 | -0.17 | -27.68 | 1/5 | não | REJECT |

Portões D3: ≥ 30 trades; DD ≤ 15%; top-5 trades ≤ 40% do lucro bruto; nenhum mês > 40% do lucro; expectância > 0. **Nenhum candidato passou em todos** ⇒ o placar top 3 continua vazio.

## Principais achados
1. **Adaptar a distância ao range não se pagou** (EXP-0009 vs controle fixo EXP-0010: mesmo PnL, DD 18,0% vs 13,5%, excesso sobre o placebo +4,6 vs +9,9, 1 vs 0 graus de liberdade): a versão simples vence.
2. **A arquitetura da literatura (stop estrutural no extremo da 1ª barra, sem trailing, segurar até 17:55) é a única com expectância positiva** (EXP-0011: +R$ 0,4/trade, excesso +R$ 26 sobre o placebo; EXP-0012 com regime de vol alta: +R$ 34/trade, PF 1,41, DD 14,3%, acima de **todos** os 10 sorteios). Mas é **frágil**: no EXP-0012 os 5 melhores trades são 72% do lucro bruto e março (+R$ 1.788) supera o lucro total (sem março: −R$ 258); no EXP-0011 o DD é 24,6% com 17 perdas seguidas.
3. **O trailing curto atrapalha**: 77–82% das saídas dos EXP-0009/0010 foram por trailing (whipsaw); o benchmark do acaso depende da arquitetura de saída (placebo de −R$ 14 a −R$ 42, ou ~0 no gap-and-go). O **excesso sobre o placebo**, não o benchmark de fórmula, é a medida correta.
4. **Dias de baixa volatilidade perdem em quatro arquiteturas diferentes** (V0, EXP-0009, 0010, 0011), mas é a mesma amostra: o filtro do EXP-0012 é **data-informed**.
5. **Sem edge**: momentum de fim de dia (agora testável; excesso +R$ 0,7), rompimento do range de 30 min (abaixo do placebo, −R$ 8), fades do V0 com payoff 1:1 (piorou) e gap-and-go (direção do gap **pior que o acaso**, −R$ 27,7; não se inverte a direção depois de perder).

## Linhagem
```
Baseline V0 (EXP-0000, idêntico no motor 1.1.0)
 ├─ (RUN-0001/EXP-0002 ORB, reaberto por mecanismo novo)
 │    └─ EXP-0009 ORB adaptativo (stop=trailing=0,25×range) ............ REJECT
 │         └─ EXP-0010 controle fixo (10 pts) .......................... REFINE  (excesso sobre o placebo +9,9)
 │              └─ EXP-0011 stop estrutural, sem trailing, EOD ......... REFINE  (única expectância > 0; frágil)
 │                   └─ EXP-0012 + regime de vol alta (data-informed) .. INCONCLUSIVE (fronteira; falha concentração)
 ├─ EXP-0013 rompimento do range de 30 min ............................. REJECT
 ├─ (RUN-0001/EXP-0008 late-day, reaberto: exit_time)
 │    └─ EXP-0014 momentum 17:30→17:55 ................................. REJECT
 ├─ (RUN-0001/EXP-0005 V0 sem canal)
 │    └─ EXP-0015 payoff 1:1 ........................................... REJECT
 └─ EXP-0016 gap-and-go com stop no preenchimento ...................... REJECT
```

## Estado dos ramos
- **Opening-Momentum: PROMISING (fraco, data-informed)** — arquitetura de saída da literatura é o único caminho com expectância positiva; falha concentração/drawdown. Trailing curto e adaptação ao range: fechados.
- **Intraday-Momentum-LateDay: NÃO SUSTENTADO** (testado corretamente). **OR30-Breakout: 1 rejeição. Gap-and-Go: 1 rejeição (excesso negativo). V0-Filters (payoff): EXPLORATORY, sem ganho.**

## Fronteira multiobjetivo (nenhum elegível ao top 3)
- **EXP-0012**: melhores métricas (PF 1,41; expectância +34; DD 14,3%; excesso +75,7) — falha top-5 (72%) e concentração mensal; 45 trades.
- **EXP-0011**: expectância positiva com 100 trades — falha DD (24,6%) e concentração.
- **EXP-0010**: mais estável (DD 13,5%, top-5 35%) e acima do placebo (+9,9), porém expectância −R$ 9,95.

## Riscos
1. **Snooping**: 16 tentativas na mesma partição; EXP-0012 nasceu da decomposição (data-informed). 2. **Amostra**: 45–100 trades; erro-padrão da expectância ≈ R$ 11+. 3. **Custos provisórios** (slippage 0,5 pt/lado); resultados dependem deles. 4. **Placebo com apenas 10 sorteios** (grosso). 5. **Série ajustada** (R6). 6. Risco de gap do stop estrutural (pior trade −R$ 267 a −R$ 547).

## Recomendação
Nenhum candidato é elegível a checkpoint de validação pelo top 3. Se você quiser gastar **1 das 3** consultas, o alvo seria a arquitetura do EXP-0011/0012, ciente do risco data-informed. Alternativa mais robusta para a Run 3: hipóteses sobre a **concentração** da arquitetura estrutural (não sobre novos limiares), com mecanismo independente, mais sorteios do placebo e, se possível, custos reais (D6).

Fontes: `research_notes.md` (RUN-0001 e RUN-0002).
