# RUN-0003 — Relatório

**Tempos:** setup ~1.9 min | experimentação ~7.9 min de 20 (encerrada antes por falta de hipótese independente e não-tuning) | fechamento ~1.3 min (análises complementares, relatório, livro, pytest completo, commit) | total ~13.4 min. **Tentativas cumulativas: 21** (16 + 5). Baseline sob o motor 1.1.0: idêntico ao da RUN-0002 (PF 0,75; PnL −R$ 1.097; 96 trades).

## Análises preparatórias e complementares (não são tentativas)
- **A — placebo de seleção do EXP-0012:** P(subconjunto aleatório de 45 dos 100 trades do EXP-0011 ≥ +R$ 34/trade) = **12,3%** (PF: 14,5%): moderado, inconclusivo; a regra é data-informed. Achado: o top-5 típico de subconjuntos desta arquitetura é **0,84** do lucro bruto (p5 = 0,70), então os 72% do EXP-0012 são normais: o portão D3 "top-5 ≤ 40%" é **estruturalmente inatingível** para arquiteturas de win rate baixo e payoff alto (proposta D10).
- **B — placebo reforçado (200 sorteios) do EXP-0011:** placebo −R$ 22,9 (sd 14,1); candidato +R$ 0,4; z = 1,66; **P(placebo ≥ candidato) = 3,5%**. O sinal de direção da 1ª barra parece conter informação, mas com 21 tentativas acumuladas não sobrevive a correção de múltiplos testes, e a expectância líquida é ≈ 0.
- **C — deriva intradiária (abertura→17:55):** média −2,4 pts, t = −0,65: **não** explica a assimetria long/short (+R$ 850/−R$ 810) do EXP-0011; fica como ruído.
- **D — sensibilidade de execução:** EXP-0011 rende **+R$ 12,4/trade sem custos e sem slippage**, +R$ 0,4 no cenário base e −R$ 9,6 com slippage de 1 pt/lado: cada 0,5 pt/lado consome ~R$ 10/trade (equilíbrio ≈ 0,55 pt/lado). EXP-0012 é positivo em todos os cenários (+R$ 24 a +46), porém data-informed.

## Experimentos (partição de pesquisa; custos provisórios)
| Exp | Candidato (pai EXP-0011) | PF | WR | PnL (R$) | Max DD | Trades | Expectância | Placebo (média, 20 sorteios) | Excesso | P(seleção ≥ cand.) | Meses + | Decisão |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0017 | ORB estrutural + volume relativo da 1ª barra | 0.856 | 23.26% | -546.0 | 21.4% | 43 | -12.7 | -34.21 | 21.51 | 0.66 | 2/5 | REJECT |
| 0018 | ORB estrutural + a favor da tendência D1 | 0.612 | 13.73% | -1867.0 | 23.02% | 51 | -36.61 | -41.38 | 4.77 | 0.93 | 1/5 | REJECT |
| 0019 | ORB estrutural + 2ª entrada após stop | 0.905 | 18.18% | -987.0 | 34.89% | 121 | -8.16 | -16.96 | 8.8 | n/a | 3/5 | REJECT |
| 0020 | ORB na abertura de NY (09:30 ET) | 0.724 | 15.22% | -1359.0 | 20.81% | 92 | -14.77 | -14.59 | -0.18 | n/a | 1/5 | REJECT |
| 0021 | ORB estrutural + alvo estrutural PDH/PDL | 0.589 | 23.0% | -3030.0 | 31.73% | 100 | -30.3 | -30.67 | 0.37 | n/a | 1/5 | REJECT |

Portões D3: nenhum passou. O placar top 3 continua vazio.

## O que aprendemos
1. **Cinco mecanismos independentes da nossa amostra, cinco resultados sem edge.** Volume relativo ("in play"), alinhamento com a tendência D1, segunda entrada, ORB na abertura de NY e alvo estrutural não melhoraram a arquitetura do EXP-0011.
2. **Filtrar ~45 dos 100 trades tem pouco poder:** subconjuntos aleatórios têm média ~0 ± R$ 48. Os filtros de volume e de tendência escolheram trades **piores que o típico** (P = 66% e 93%).
3. **A arquitetura depende de poucos vencedores grandes:** qualquer teto (alvo fixo, alvo estrutural) ou reentrada piora; não capar nem alavancar.
4. **A informação de direção parece específica da abertura da B3** (a barra das 09:30 ET não tem excesso sobre o acaso).
5. **O gargalo é a execução:** o edge bruto (~R$ 12/trade) é do tamanho do custo; slippage real menor que 0,55 pt/lado é pré-requisito. D6 (custos reais) passa a ser decisivo.
6. Sem novas hipóteses derivadas de long/short ou de metades do período (sem mecanismo independente).

## Linhagem
```
Baseline V0 (EXP-0000)
 └─ RUN-0002/EXP-0011 (ORB 5 min, stop estrutural, sem trailing, saída 17:55)  ← arquitetura da fronteira
      ├─ EXP-0017 + volume relativo ............ REJECT
      ├─ EXP-0018 + a favor da tendência D1 .... REJECT
      ├─ EXP-0019 + 2ª entrada após stop ....... REJECT
      ├─ EXP-0020 na abertura de NY ............ REJECT
      ├─ EXP-0021 + alvo estrutural PDH/PDL .... REJECT
      └─ EXP-0022 breakeven condicional ........ BLOCKED (capacidade do motor; D11)
```

## Estado dos ramos e fronteira
- **Opening-Momentum: PROMISING (fraco, data-informed)** sem mudança: fronteira continua EXP-0012 (data-informed) e EXP-0011. **Famílias fechadas nesta run:** filtro de volume relativo, alinhamento de tendência (continuação), multi-trade (1 re-entrada), abertura de NY, alvo estrutural.
- Top 3: vazio. Nenhum candidato elegível a checkpoint de validação.

## Riscos
1. **Snooping:** 21 tentativas (+ 4 análises) sobre ≤ 100 trades. 2. **Custos provisórios** (o resultado depende de slippage < 0,55 pt/lado). 3. **Placebo de 20 sorteios** (200 na Análise B). 4. **Série ajustada** (R6). 5. Sem hipótese independente restante que justifique mais tentativas.

## Decisões pendentes para você
- **D10 (novo): portão de concentração.** O top-5 ≤ 40% do lucro bruto é inatingível para arquiteturas de win rate baixo/payoff alto (mediana do acaso: 0,84). Proposta: substituir/complementar por uma comparação com o percentil do placebo de seleção (ou normalizar pelo nº de vencedores). Não alterei o portão.
- **D11 (novo): capacidade condicional de saída no motor** (breakeven/ativação do trailing após +X pontos): desbloqueia o EXP-0022.
- **Validação:** nenhum candidato é elegível pelo top 3; se quiser gastar 1 das 3 consultas, o alvo seria a arquitetura EXP-0011/0012, ciente do risco data-informed.
- **Custos reais (D6)** têm agora valor decisivo.
