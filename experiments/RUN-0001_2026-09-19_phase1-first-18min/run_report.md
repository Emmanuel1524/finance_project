# RUN-0001 — Relatório (primeiro teste da Fase 1; parcial)

Tempo usado: 10 min 47 s de 18 min. 8 experimentos (de um teto de 25); parei por falta de ideias materialmente diferentes que não virassem ajuste fino ou empilhamento post-hoc.

## Baseline V0 (partição de pesquisa, custos provisórios)
PF 0.75 | WR 57.29% | PnL R$ -1097.0 | MaxDD 16.98% | Trades 96 | Payoff 0.559 | Exp R$ -11.43 | 0/5 meses positivos | reprova em drawdown (17% > 15%), concentração mensal (lucro total negativo) e expectância.
Por padrão: P3 (canal) é o que mais perde (25 trades, -R$915; win rate 33-50%); P4_RSI é o único positivo (13 trades, +R$104, win rate 69%).

## Achado central: o benchmark de "entrada sem edge"
Com stop 10 / alvo 6 uma entrada sem edge acerta ~62,5% (10/16) e, com ~1,2 pt de custo por trade, perde ~R$12/trade. Todos os candidatos ficam perto disso
(expectância entre -R$2 e -R$14 com n ≤ 100; erro-padrão do win rate ≈ 5 p.p.): **nenhum mostra edge estatisticamente distinguível**. O payoff estrutural 0,6 é o gargalo;
mudar a estrutura de saída exige suporte do motor (só há stop/alvo fixos).

## Experimentos
| Exp | Candidato | Pai | PF | Win rate | PnL (R$) | Max DD | Trades | Expectância (R$) | Meses + | Portões D3 | Decisão |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0000 | Baseline V0 | - | 0.75 | 57.29% | -1097.0 | 16.98% | 96 | -11.43 | 0/5 | não | baseline |
| 0001 | V0 + filtro baixa vol | V0 | 0.846 | 58.14% | -296.0 | 8.67% | 43 | -6.88 | 1/5 | não | REJECT |
| 0002 | Opening momentum (ORB 5min) | V0 | 0.786 | 59.0% | -940.0 | 11.51% | 100 | -9.4 | 3/5 | não | REFINE |
| 0003 | ORB payoff 2:1 | 0002 | 0.775 | 30.3% | -1683.0 | 23.99% | 99 | -17.0 | 0/5 | não | REJECT |
| 0004 | V0 alinhado à tendência D1 | V0 | 0.706 | 57.35% | -911.0 | 14.74% | 68 | -13.4 | 1/5 | não | REJECT |
| 0005 | V0 sem canal (P3) | V0 | 0.937 | 61.97% | -182.0 | 10.97% | 71 | -2.56 | 2/5 | não | REFINE |
| 0006 | V0 sem canal + vol alta | 0005 | 0.947 | 60.0% | -80.0 | 7.06% | 35 | -2.29 | 2/5 | não | REJECT |
| 0007 | Fade fora do range (sem IFR) | V0 | 0.738 | 52.94% | -224.0 | 4.84% | 17 | -13.18 | 2/5 | não | REJECT |
| 0008 | Momentum fim de dia (17:30) | V0 | 0.651 | 55.56% | -2338.0 | 26.95% | 99 | -23.62 | 1/5 | não | REJECT (design inválido) |

Portões D3: ≥ 30 trades; drawdown ≤ 15%; top-5 trades ≤ 40% do lucro bruto; nenhum mês > 40% do lucro; expectância > 0. **Nenhum candidato passou** ⇒ o placar top 3 permanece vazio (resultado válido).

## Linhagem
```
Baseline V0 (EXP-0000)
 ├─ EXP-0001 vol-gate ........................ REJECT   (ramo V0-Filters)
 ├─ EXP-0002 ORB 5min ........................ REFINE   (ramo Opening-Momentum)
 │    └─ EXP-0003 payoff 2:1 ................. REJECT   → ramo FECHADO
 ├─ EXP-0004 alinhado à tendência D1 ......... REJECT   (V0-Filters)
 ├─ EXP-0005 sem canal (P3) .................. REFINE   (V0-Filters) → PROMISING, com ressalva post-hoc
 │    └─ EXP-0006 + vol alta ................. REJECT   (complexidade não compensa; concentração 39,5%)
 ├─ EXP-0007 fade fora do range sem IFR ...... REJECT   (Range-Exhaustion; n=17 inconclusivo)
 └─ EXP-0008 momentum de fim de dia .......... REJECT   (design inválido: sem saída por horário no motor)
```

## Estado dos ramos
- **Opening-Momentum: CLOSED** (ORB sem excesso de edge nem com payoff 0,6 nem 2:1; reabrir só com racional novo).
- **V0-Filters: PROMISING (fraco)**: EXP-0005 domina o V0 em PF/PnL/drawdown, mas expectância ainda negativa e hipótese post-hoc.
- **Range-Exhaustion: EXPLORATORY** (uma rejeição; amostra pequena, inconclusiva).
- **Intraday-Momentum-LateDay: EXPLORATORY/INCONCLUSIVO** (não testável sem saída por horário).

## Fronteira multiobjetivo (nenhuma passa nos portões)
- **EXP-0005**: melhor equilíbrio (PF 0,937; PnL -R$182; DD 11,0%; 71 trades; expectância -R$2,56).
- **EXP-0006**: menor drawdown com ≥ 30 trades (7,1%) e PF 0,947, mas 35 trades e top-5 = 39,5% (frágil).
- **EXP-0001**: PF 0,846; DD 8,7%; 43 trades; mais simples que 0006.

## Principais riscos e fraquezas
1. **Post-hoc**: EXP-0001/0004/0005/0006/0007 foram motivados pela decomposição do V0 na própria pesquisa; sem validação, o risco de overfit é alto (e é o argumento para não promover EXP-0005 ainda).
2. **Amostra pequena**: ≤ 100 trades em 5 meses; ICs largos. **Custos provisórios**: resultados dependem de D6; com custo maior tudo piora.
3. **Estrutura de saída** (payoff 0,6) e **risco de gap** (pior trade -R$107 a -R$642).
4. **Série ajustada** (R6): níveis PDH/PDL podem diferir do que o robô via.
5. Não há tempo-de-saída no motor: bloqueia toda uma classe de hipóteses (fim de dia, time-stop).

## Candidatos adequados à Fase 2?
**Nenhum ainda.** Nenhum candidato tem expectância positiva; otimizar parâmetros agora seria otimizar ruído. Próximos passos sugeridos ao usuário: (a) informar custos/slippage reais (D6); (b) decidir se aprova uma capacidade de saída por horário/EOD no motor (tarefa separada, 05 §10); (c) autorizar, se quiser, **uma** consulta à validação para EXP-0005 (consome 1 das 3); (d) nova run de descoberta com foco em estrutura de saída e em novas famílias.

Fontes: ver `research_notes.md`.
