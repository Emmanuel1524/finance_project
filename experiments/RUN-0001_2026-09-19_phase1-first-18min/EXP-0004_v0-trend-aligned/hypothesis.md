# EXP-0004 — V0 alinhado à tendência diária (trend-aligned)
Pai: EXP-0000. Ramo: V0-Filters. Família: alinhamento de tendência.
**Hipótese:** os fades contra-tendência do V0 são estruturalmente mais fracos; operar apenas a favor da tendência dos candles D1 fechados
(abertura acima das 3 EMAs D1 = só compras; abaixo das 3 = só vendas; entre elas = sem filtro) elimina os trades de pior qualidade.
**Racional:** pullback a favor da tendência (fade dentro da tendência) tem melhor assimetria que fade contra ela; filtros de tendência são padrão em EAs intradiários.
Nota: a decomposição do V0 mostrou LONG bem pior que SHORT (formulação pós-decomposição; validar depois).
**Fraqueza do pai que ataca:** trades contra a tendência dominante.
**Mudança:** V0TrendAligned = V0 com descarte de ordens do lado contrário à tendência D1. Nenhum parâmetro novo.
