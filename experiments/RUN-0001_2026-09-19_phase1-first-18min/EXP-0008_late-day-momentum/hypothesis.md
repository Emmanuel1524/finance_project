# EXP-0008 — Momentum intradiário de fim de dia (1ª meia hora -> última meia hora)
Pai: EXP-0000 (exploração, família nova). Ramo: Intraday-Momentum-LateDay. Família: momentum intradiário.
**Hipótese:** o retorno da 1ª meia hora (fechamento anterior -> 09:30) prevê a direção do fim do dia; entrar às 17:30 na direção de r1.
**Racional:** Gao, Han, Li, Zhou (JFE 2018): previsão estatística e econômica, mais forte em dias voláteis (evidência em ETFs de índice; WDO não testado).
**Fraqueza do pai que ataca:** o V0 só opera a abertura e não tem edge; testa outra janela do dia, sem depender das regras do V0.
**Mudança:** LateDayMomentum; Config do candidato: janela de sessão 09:00-18:00 (só para a estratégia enxergar as barras do dia); entrada única às 17:30; saídas do V0 (10/6).
Limitações: saídas fixas 10/6 não coincidem com 'manter até o fechamento'; horário de pregão do WDO até 18:00 assumido; posição pode passar a noite se não atingir stop/alvo.
