# EXP-0003 — Opening momentum com estrutura de saída de payoff positivo
Pai: EXP-0002. Ramo: Opening-Momentum. Família: momentum + arquitetura de saída.
**Hipótese:** o lucro de momentum vem de movimentos ocasionais grandes; o alvo de 6 pts (payoff 0,6) trunca os ganhos e deixa o custo
dominar (entrada aleatória perde ~R$12/trade com 10/6). Mudança estrutural do perfil de payoff: manter o stop de 10 pts e levar o alvo a
20 pts (payoff 2:1), única variante testada (não é busca).
**Racional:** estratégias de continuação/ORB tendem a ter assimetria positiva (muitos stops pequenos, poucos ganhos grandes); Zarattini & Aziz usam saída no fim do dia, não alvo curto.
**Fraqueza do pai que ataca:** payoff < 1 com custos fixos.
**Mudança:** mesma entrada do EXP-0002; Config gain_points=20 (stop 10 inalterado). Motor e custos inalterados.
