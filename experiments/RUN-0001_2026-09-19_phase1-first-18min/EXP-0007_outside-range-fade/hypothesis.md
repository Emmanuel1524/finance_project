# EXP-0007 — Fade de abertura fora do range do dia anterior (sem IFR)
Pai: EXP-0000 (exploração). Ramo: Range-Exhaustion. Família: reversão de exaustão overnight.
**Hipótese:** o P4 do V0 (13 trades, win rate 69%, único componente acima do benchmark de 62,5%) pode dever seu acerto à exaustão do movimento overnight (abertura fora da PDH/PDL) e não ao filtro de IFR.
**Racional:** níveis do dia anterior como referência de liquidez; gaps para fora do range tendem a reverter parcialmente. Contra: estudo arXiv 2605.04004 (MNQ): fade de gap falha em todos os horários testados.
**Fraqueza do pai que ataca:** o V0 mistura famílias; testa a família mais promissora isolada e sem o filtro de IFR.
**Mudança:** OutsideRangeFade: a mercado na abertura da 1ª barra contra a abertura fora do range; sem IFR/canal/médias; saídas do V0.
