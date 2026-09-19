# EXP-0017 — ORB estrutural (EXP-0011) só com volume relativo alto da 1ª barra ("in play")
Pai: RUN-0002/EXP-0011 (arquitetura da fronteira). Ramo: Opening-Momentum. Família: momentum + filtro de participação.
**Checagem de novidade (knowledge.md):** volume nunca foi usado; sem linha equivalente.
**hypothesis_source:** literatura (Zarattini, Barbon & Aziz 2024, "stocks in play": ORB funciona melhor quando o volume relativo de abertura é alto) + mecanismo (participação informada favorece a continuação da 1ª barra). INDEPENDENTE da nossa amostra.
**Premissa desafiada:** operar todos os dias com o mesmo critério de qualidade do sinal.
**Reabertura:** (i) mecanismo novo — filtro independente do regime de volatilidade (o EXP-0012 usa range do dia anterior; este usa volume da 1ª barra).
**Hipótese:** o sinal de continuação é mais confiável quando o volume da 1ª barra excede a mediana dos volumes das 1ªs barras das 20 sessões anteriores; sem 10 sessões de histórico não opera.
**Os 4 pontos:** (i) o sinal de 1 barra é ruidoso e a participação varia por dia; (ii) filtrar por volume relativo da 1ª barra (mediana de 20 sessões passadas, mesma janela do D7, sem novo limiar), mesma saída do EXP-0011; (iii) filtro por outra variável (volume), não vizinho numérico; (iv) sustenta: expectância > 0 e acima do placebo, com placebo de seleção favorável e portões avaliados; rejeita: caso contrário.
Graus de liberdade: 0 (janela 20 e histórico mínimo 10 reutilizam D7). Ressalva: colunas de volume do arquivo MT5 (`VOL`, volume real), série ajustada (R6).
