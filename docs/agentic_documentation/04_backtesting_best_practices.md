# 04 — Práticas de backtesting de alto nível

Princípio: **um backtest é uma hipótese sobre o passado, não uma prova sobre o futuro**. O trabalho do engenheiro quant é tentar *quebrar* o resultado antes que o mercado o faça.

## 1. Vieses que invalidam resultados

| Viés | Descrição | Defesa neste projeto |
|---|---|---|
| **Look-ahead** | Usar informação indisponível no instante da decisão (barra em formação, fechamento do dia, EMA calculada com barras futuras) | Indicadores só com dados ≤ t−1; checklist de vazamentos em [05 §5](05_replay_trading_guide.md) e testes de [05 §11](05_replay_trading_guide.md) |
| **Survivorship** | Só ver ativos/contratos que "sobreviveram" | Rollover explícito; documentar contratos usados |
| **Data snooping / p-hacking** | Testar muitas variantes e reportar a melhor | Registrar nº de configs testadas; correção para múltiplos testes |
| **Overfitting** | Parâmetros ajustados ao ruído da amostra | Walk-forward, estabilidade de vizinhança, holdout |
| **Selection bias de período** | Escolher janela favorável | Períodos definidos a priori; reportar todos |
| **Execução otimista** | Assumir fills perfeitos | `adverse`, slippage, custos, sem preço "no meio" |
| **Regime change** | Edge existe só em um regime | Análise por regime e por subperíodo |
| **Custo omitido** | Ignorar corretagem, emolumentos, slippage | Custos obrigatórios em toda métrica financeira |

## 2. Anatomia de um backtest correto

1. **Hipótese econômica** antes do código (por que o edge deveria existir? quem está do outro lado?).
2. **Dados** validados, versionados, com timezone e calendário corretos.
3. **Point-in-time**: cada decisão em t enxerga só o que existia em t.
4. **Modelo de execução** realista (ver 05).
5. **Custos** e restrições (tick, lote, horário, limites de risco).
6. **Divisão temporal** pesquisa / validação / holdout — nunca aleatória; política em [06 §6](06_quant_finance_playbook.md).
7. **Métricas** + intervalos de confiança + análise de sensibilidade.
8. **Reprodutibilidade**: mesmo dado + config + código = mesmo resultado.
9. **Relatório honesto** incluindo o que não funcionou.

## 3. Validação temporal

- **Pesquisa / validação / holdout final**: definições e regras de acesso em [06 §6](06_quant_finance_playbook.md) (o holdout é invisível na Fase 1 e aberto **uma única vez**).
- **Walk-forward** (**Fase 2**): otimiza em janela [t0,t1], testa em [t1,t2], rola. Reportar desempenho concatenado só dos períodos out-of-sample.
- **Purging e embargo** (López de Prado) se houver features com janela de rótulo sobreposta.
- **CPCV** (combinatorial purged cross-validation) quando houver amostra suficiente e modelos de ML.
- Estratégias de 1 trade/dia geram amostra pequena (~1 trade por dia útil ≈ ≤170 em 8 meses, **estimativa**): use bootstrap por bloco e desconfie de qualquer métrica com IC largo.

## 4. Robustez

- **Sensibilidade paramétrica** (**somente Fase 2**, sobre uma arquitetura já escolhida): varrer `gain`, `loss`, `offset`, tolerância EMA, faixas RSI. Procure *platôs*, não picos. Na Fase 1 não se varrem limiares ([06 §2](06_quant_finance_playbook.md)).
- **Sensibilidade de execução** (vale nas duas fases; é teste de robustez, não otimização; mesma grade para todos os candidatos): slippage 0 / 0,5 / 1 / 2 pts; `intrabar_policy` = `adverse` vs `target_first`; atraso de 1 barra na entrada.
- **Perturbação de dados**: jitter nos preços dentro do tick, remoção aleatória de dias, troca de contrato.
- **Placebo / controles**: mesma lógica com direção invertida, com datas embaralhadas, com sinais aleatórios de mesma frequência. Edge real não sobrevive ao placebo.
- **Subperíodos**: por mês, por trimestre, por dia da semana, por regime de volatilidade, dias de evento (Copom, payroll, FOMC).

## 5. Estatística mínima exigida

- **Sharpe/Sortino** em retornos diários (não anualizar sem declarar o fator).
- **Deflated Sharpe Ratio** e/ou **Probability of Backtest Overfitting (PBO)** quando houver seleção de parâmetros.
- **Bootstrap** (por trade e por bloco) para IC de PnL médio, win rate, profit factor.
- **Teste de hipótese** do expected payoff > 0 com correção para múltiplos testes.
- Reportar **expectativa em pontos e em R$**, e **breakeven win rate** (com alvo 6 / stop 10 e custo zero: `10/(6+10)` = 62,5%; **com custos, mais alto**).

## 6. Métricas — definições que este projeto usa

- **Profit Factor** = lucro bruto / |perda bruta|.
- **Expected Payoff** = PnL médio por trade.
- **Payoff Ratio** = ganho médio / |perda média|.
- **Max Drawdown** = maior queda do pico da curva de equity (R$ e %).
- **Recovery Factor** = lucro líquido / |max drawdown|.
- **MAE/MFE**: máxima excursão adversa/favorável por trade — base para calibrar stop/alvo.
- **Exposição** = % do tempo em posição.

## 7. Auditoria e testes de correção do próprio backtester

Um backtester também precisa ser testado como software:

- **Testes unitários** por regra, com barras sintéticas e resultado calculado à mão.
- **Testes de invariantes** (property-based): ≤1 posição, PnL contábil bate, stop/alvo no lado certo.
- **Teste de look-ahead**: resultado em t não muda ao alterar dados posteriores a t.
- **Golden file**: trades de referência versionados; mudanças exigem justificativa.
- **Paridade com a plataforma real** (MT5 Strategy Tester "cada tick com base em ticks reais"): comparar lista de trades e explicar cada divergência.
- **Trilha de eventos**: todo `ENTRY/EXIT/cancelamento` com motivo textual.

## 8. Reporte de resultados (template)

Todo resultado apresentado deve conter: período, fonte e hash do dado, `Config` completa, custos/slippage, nº de trades, métricas + IC, sensibilidade, limitações, e o commit/versão do código. Sem isso, o número é decorativo.
