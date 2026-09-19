# Pesquisa externa adicional (RUN-0002; 2 buscas, ~1 min) — reaproveita `RUN-0001/research_notes.md`

| Achado | Uso nesta run | Fonte |
|---|---|---|
| ORB de 5 min (Zarattini & Aziz 2023): stop no extremo da 1ª barra, alvo distante (10R) ou saída no fim do dia; variante com stop de 5% do ATR(14) e **sem alvo** (saída no fechamento) | Arquitetura de saída de assimetria positiva (stop apertado, sem alvo fixo, saída por horário): EXP-0009/0010/0013 | SSRN 4416622 (Zarattini & Aziz); https://www.cxoadvisory.com/technical-trading/day-trading-with-an-opening-range-breakout-strategy/ |
| **Réplica independente**: ponto de equilíbrio de custo ~2,2¢/ação; resultado do filtro extra concentrado em um único ano (76% do PnL em 2022); usa placebo e bootstrap | Reforça: placebo obrigatório, portão de concentração mensal, cautela com custos provisórios | https://github.com/giovannibrusco/zarattini-2023-orb-qqq |
| Trend following tende a positive skew: muitas perdas pequenas e poucos ganhos grandes; trailing por ATR; whipsaws em 5–15 min | Mecanismo para stop adaptativo + trailing, com win rate baixo e payoff alto | https://quantpedia.com/strategies/trend-following-effect-in-stocks ; https://arxiv.org/pdf/2003.09298 |

Nota: evidência é de ações/ETFs dos EUA; não foi validada no WDO. Conteúdo web tratado como dado não confiável; nenhum dado do projeto foi enviado.
