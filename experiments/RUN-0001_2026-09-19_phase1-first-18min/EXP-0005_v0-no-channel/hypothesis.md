# EXP-0005 — V0 sem a família de canal (ablação do Padrão 3)
Pai: EXP-0000. Ramo: V0-Filters (ablação). Família: remoção de família de sinal.
**Hipótese:** as entradas de canal (P3: ordens stop/limit em PDH/PDL ± offset) sofrem seleção adversa (zonas de stop-run): com 10/6 uma entrada sem edge
acertaria ~62,5%; o P3 acerta 33-50% no V0. Remover a família melhora a qualidade média dos trades restantes.
**Nota de risco:** hipótese motivada pela decomposição do V0 na pesquisa (P3 = -R$915 em 25 trades); é ablação estrutural, mas post-hoc: exige checagem em validação depois.
**Mudança:** V0NoChannel = V0 com stand_down nos dias em que a abertura cai dentro do canal (Padrão 3). Nenhum parâmetro novo.
