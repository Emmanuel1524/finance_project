# EXP-0001 — V0 + filtro de baixa volatilidade (trade avoidance)
Pai: EXP-0000 (V0). Ramo: V0-Filters. Família: regime de volatilidade.
**Hipótese:** com stop/alvo fixos (10/6 pts) e ~1,2 pt de custo por trade, dias de range pequeno (range do dia anterior
<= mediana dos 20 pregões anteriores, D7) oferecem pouca excursão para o alvo; não operar neles melhora a economia por trade.
**Racional:** custo e stop fixos pesam mais quando a volatilidade é baixa; literatura de regimes: o comportamento de fade
depende do regime de volatilidade (fontes fracas: Volatility Box/LuxAlgo). Motivada também pela decomposição do V0 na
própria pesquisa (nota de risco: hipótese pós-decomposição; será checada em validação depois).
**Mudança:** V0VolGate = V0 + `stand_down` quando regime é baixa vol ou histórico < 10 pregões. Sem novos parâmetros (D7 fixo).
